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
import os
import traceback
from typing import Any, Callable, ClassVar, Dict, List, Optional, TYPE_CHECKING, Tuple

import sys

from .abc import ItemContainer
from .item import ModalItem
from ..enums import ComponentType, InteractionType
from ..utils import MISSING

if TYPE_CHECKING:
    from ..interactions import Interaction
    from ..state import ConnectionState

    Kwargs = Dict[str, Any]
    ModalItemConstructor = Callable[[], ModalItem]

__all__ = (
    'Modal',
)


class Modal(ItemContainer[ModalItem], max_width=1, max_children=5):
    """Represents a UI modal.

    This can only be used as a modal response to a :class:`~.Interaction`.

    Usage ::

        .. code:: python3

            import discord
            from discord.ui import Modal, text_input

            class MyModal(Modal):
                name = text_input(label='Name', placeholder='Enter your name here...', min_length=2, max_length=32, required=True)

                def __init__(self):
                    super().__init__(title='My Modal', timeout=240)

                async def callback(self, interaction: discord.Interaction):
                    await interaction.response.send_message(f'Hello, {self.name.value}!')

            class Hello(discord.application_commands.ApplicationCommand):
                \"""Sends a modal\"""

                async def callback(self, interaction: discord.Interaction):
                    await interaction.response.send_modal(MyModal())

    .. versionadded:: 2.0

    Parameters
    ----------
    title: str
        The title of this modal. This parameter is required.
    custom_id: str
        The ID of the modal that gets received during an interaction.
    timeout: Optional[:class:`float`] = None
        Timeout in seconds before the client will no longer accept modal submissions.
        If ``None`` (default) then there is no timeout.

    Attributes
    ----------
    title: str
        The title of this modal.
    custom_id: Optional[:class:`str`]
        The ID of the modal that gets received during an interaction.
    timeout: Optional[:class:`float`]
        Timeout in seconds before the client will no longer accept modal submissions.
        If ``None`` then there is no timeout.
    children: List[:class:`Item`]
        The list of children attached to this modal.
    """

    __discord_ui_modal_children__: ClassVar[List[ModalItemConstructor]] = []

    # noinspection PyMethodOverriding
    def __init_subclass__(cls, **kwargs) -> None:
        children = []
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if (
                    hasattr(member, '__discord_ui_model_type__')
                    and issubclass(member.__discord_ui_model_type__, ModalItem)
                ):
                    member.__discord_ui_attribute_name__ = name
                    children.append(member)

        if len(children) > cls.__discord_ui_max_children__:
            raise TypeError(f'Modal cannot have more than {cls.__discord_ui_max_children__} children.')

        cls.__discord_ui_modal_children__ = children

    def __init__(self, *, title: str = MISSING, custom_id: str = MISSING, timeout: Optional[float] = None) -> None:
        self.title: str = title
        self.custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id

        super().__init__(timeout=timeout)

        # Store type as int as we will access with an int (from raw payload)
        self._children_mapping: Dict[Tuple[int, str], ModalItem] = {}
        for child in self.__discord_ui_modal_children__:
            self.add_item(c := child())
            setattr(self, child.__discord_ui_attribute_name__, c)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} timeout={self.timeout} children={len(self.children)} title={self.title!r}>'

    async def on_error(self, error: Exception, interaction: Interaction):
        """|coro|

        The callback for when an error occurs in the :meth:`callback` of this modal.
        The default implementation prints the traceback to stderr.

        Parameters
        -----------
        error: :class:`Exception`
            The error that occurred.
        interaction: :class:`.Interaction`
            The interaction that submitted this Modal.
        """
        print(f"Ignoring exception in modal {self}:", file=sys.stderr)
        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    def add_item(self, item: ModalItem) -> None:
        if hasattr(item, 'custom_id'):
            self._children_mapping[item.type.value, item.custom_id] = item  # type: ignore

        super().add_item(item)

    def remove_item(self, item: ModalItem) -> None:
        # noinspection PyUnresolvedReferences
        if hasattr(item, 'custom_id') and (item.type, item.custom_id) in self._children_mapping:
            del self._children_mapping[item.type.value, item.custom_id]  # type: ignore

        super().remove_item(item)

    async def callback(self, interaction: Interaction):
        """|coro|

        The method that is called when the user responds to this modal.

        Parameters
        ----------
        interaction: :class:`~.Interaction`
            The interaction that triggered this modal.
        """
        pass

    def _dispatch_timeout(self):
        if self.__stopped.done():
            return

        self.__stopped.set_result(True)
        asyncio.create_task(self.on_timeout(), name=f'discord-ui-modal-timeout-{self.custom_id}')

    def to_dict(self) -> Dict[str, Any]:
        """Returns this modal as a modal payload to be sent to Discord."""
        return {
            'title': self.title,
            'custom_id': self.custom_id,
            'components': self.to_components(),
        }


class ModalStore:
    def __init__(self, state: ConnectionState):
        self._modals: Dict[str, Modal] = {}
        self._state: ConnectionState = state

    def add_modal(self, modal: Modal):
        self._cleanup()
        self._modals[modal.custom_id] = modal

    def remove_modal(self, custom_id: str):
        self._modals.pop(custom_id)

    def _cleanup(self) -> None:
        for key, modal in self._modals.items():
            if modal.is_finished():
                del self._modals[key]

    @staticmethod
    async def invoke(modal: Modal, interaction: Interaction) -> None:
        if not await modal.interaction_check(interaction):
            return
        try:
            await modal.callback(interaction)
        except Exception as exc:
            await modal.on_error(exc, interaction)

    def dispatch(self, interaction: Interaction) -> None:
        self._cleanup()
        assert interaction.type is InteractionType.modal_submit

        key = interaction.data['custom_id']
        try:
            modal = self._modals[key]
        except KeyError:
            raise RuntimeError(f'received unknown modal with ID {key!r} but it is not stored.')

        for row in interaction.data['components']:
            for child in row['components']:
                if 'custom_id' not in child:
                    continue

                modal._children_mapping[child['type'], child['custom_id']]._inject_data(child)  # type: ignore

        asyncio.create_task(self.invoke(modal, interaction), name=f'discord-ui-modal-callback-{key}')
