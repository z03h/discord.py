"""
The MIT License (MIT)

Copyright (c) 2021-present Rapptz & jay3332

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from itertools import groupby
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    TYPE_CHECKING,
    TypeVar,
    Union,
    overload
)

from .item import Item, ModalItem, ViewItem
from .weights import ItemWeights

if TYPE_CHECKING:
    from ..components import (
        Component,
        ActionRow as ActionRowComponent,
        Button as ButtonComponent,
        SelectMenu as SelectComponent,
        TextInput as TextInputComponent,
    )
    from ..interactions import Interaction

    AnyComponent = TypeVar('AnyComponent', bound=Component, covariant=True)

I = TypeVar('I', bound=Item, covariant=True)

__all__ = (
    'ItemContainer',
)


def _walk_all_components(components: Iterable[AnyComponent]) -> Iterator[AnyComponent]:
    for item in components:
        if isinstance(item, ActionRowComponent):
            yield from item.children
        else:
            yield item


@overload
def _component_to_item(component: Union[ButtonComponent, SelectComponent]) -> ViewItem:
    ...


@overload
def _component_to_item(component: TextInputComponent) -> ModalItem:
    ...


def _component_to_item(component: AnyComponent) -> Item:
    if isinstance(component, ButtonComponent):
        from .button import Button

        return Button.from_component(component)
    if isinstance(component, SelectComponent):
        from .select import Select

        return Select.from_component(component)
    if isinstance(component, TextInputComponent):
        from .text_input import TextInput

        return TextInput.from_component(component)
    return Item.from_component(component)


class ItemContainer(ABC, Generic[I]):
    """Represents a container of UI components that will be displayed to the user.

    The following classes inherit from this ABC:

    - :class:`ui.View`
    - :class:`ui.Modal`

    .. versionadded:: 2.0

    Parameters
    ----------
    timeout: Optional[:class:`float`]
        The time in seconds before the client will stop responding to any input related to this container.
        Set to ``None`` to have no timeout.

    Attributes
    ----------
    timeout: Optional[:class:`float`]
        The time in seconds before the client will stop responding to any input related to this container.
        If ``None`` then there is no timeout.
    """

    if TYPE_CHECKING:
        __discord_ui_max_width__: ClassVar[int]
        __discord_ui_max_children__: ClassVar[int]

        timeout: Optional[float]
        children: List[I]

    def __init_subclass__(cls, *, max_width: int = 5, max_children: int = 25) -> None:
        cls.__discord_ui_max_width__ = max_width
        cls.__discord_ui_max_children__ = max_children

    def __init__(self, *, timeout: Optional[float] = None) -> None:
        self.timeout: Optional[float] = timeout
        self.children: List[I] = []

        self.__weights = ItemWeights(self.children, max_width=self.__discord_ui_max_width__)

        self.__cancel_callback: Optional[Callable[[ItemContainer], None]] = None
        self.__timeout_expiry: Optional[float] = None
        self.__timeout_task: Optional[asyncio.Task[None]] = None

        loop = asyncio.get_event_loop()
        self.__stopped: asyncio.Future[bool] = loop.create_future()

    async def __timeout_task_impl(self) -> None:
        while True:
            # Guard just in case someone changes the value of the timeout at runtime
            if self.timeout is None:
                return

            if self.__timeout_expiry is None:
                return self._dispatch_timeout()

            # Check if we've elapsed our currently set timeout
            now = time.monotonic()
            if now >= self.__timeout_expiry:
                return self._dispatch_timeout()

            # Wait N seconds to see if timeout data has been refreshed
            await asyncio.sleep(self.__timeout_expiry - now)

    @property
    def _expires_at(self) -> Optional[float]:
        if self.timeout:
            return time.monotonic() + self.timeout

        return None

    @abstractmethod
    def _dispatch_timeout(self):
        raise NotImplementedError

    def to_components(self) -> List[Dict[str, Any]]:
        def key(item: Item) -> int:
            return item._rendered_row or 0

        children = sorted(self.children, key=key)
        components: List[Dict[str, Any]] = []
        for _, group in groupby(children, key=key):  # type: ignore
            children = [item.to_component_dict() for item in group]
            if not children:
                continue

            components.append(
                {
                    'type': 1,
                    'components': children,
                }
            )

        return components

    async def interaction_check(self, interaction: Interaction) -> bool:
        """|coro|

        A callback that is called when an interaction happens within the the items in this container
        that checks whether it should process item callbacks for the interaction.

        This is useful to override if, for example, you want to ensure that the
        interaction author is a given user.

        The default implementation of this returns ``True``.

        .. note::

            If an exception occurs within the body then the check
            is considered a failure and :meth:`on_error` is called.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction that occurred.

        Returns
        ---------
        :class:`bool`
            Whether the children's callbacks should be called.
        """
        return True

    async def on_timeout(self) -> None:
        """|coro|

        A callback that is called when a view's timeout elapses without being explicitly stopped.
        """
        pass

    def stop(self) -> None:
        """Stops listening to interaction events from this container.

        This operation cannot be undone.
        """
        if not self.__stopped.done():
            self.__stopped.set_result(False)

        self.__timeout_expiry = None
        if self.__timeout_task is not None:
            self.__timeout_task.cancel()
            self.__timeout_task = None

        if self.__cancel_callback:
            self.__cancel_callback(self)
            self.__cancel_callback = None

    def is_finished(self) -> bool:
        """:class:`bool`: Whether the view has finished interacting."""
        return self.__stopped.done()

    async def wait(self) -> bool:
        """Waits until the view has finished interacting.

        A view is considered finished when :meth:`stop` is called
        or it times out.

        Returns
        --------
        :class:`bool`
            If ``True``, then the view timed out. If ``False`` then
            the view finished normally.
        """
        return await self.__stopped

    def add_item(self, item: I) -> None:
        """Adds an item to the view.

        Parameters
        -----------
        item: :class:`Item`
            The item to add to the view.

        Raises
        --------
        TypeError
            An :class:`Item` was not passed.
        ValueError
            Maximum number of children has been exceeded
            or the row the item is trying to be added to is full.
        """

        if len(self.children) > self.__discord_ui_max_children__:
            raise ValueError('maximum number of children exceeded')

        if not isinstance(item, Item):
            raise TypeError(f'expected Item not {item.__class__!r}')

        self.__weights.add_item(item)

        item._attach_container(self)
        self.children.append(item)

    def remove_item(self, item: I) -> None:
        """Removes an item from the view.

        Parameters
        -----------
        item: :class:`Item`
            The item to remove from the view.
        """

        try:
            self.children.remove(item)
        except ValueError:
            pass
        else:
            self.__weights.remove_item(item)

    def clear_items(self) -> None:
        """Removes all items from the view."""
        self.children.clear()
        self.__weights.clear()
