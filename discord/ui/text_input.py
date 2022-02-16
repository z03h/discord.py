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

import os
from typing import Any, Dict, Optional, TYPE_CHECKING, TypeVar, overload

from .item import ModalItem
from ..components import TextInput as TextInputComponent
from ..enums import ComponentType, TextInputStyle
from ..utils import MISSING

if TYPE_CHECKING:
    from .modal import Modal

    M = TypeVar('M', bound=Modal, covariant=True)
else:
    M = TypeVar('M', bound='Modal', covariant=True)

__all__ = (
    'TextInput',
    'text_input',
)


class TextInput(ModalItem[M]):
    """Represents a UI text input field on a modal.

    .. versionadded:: 2.0

    Parameters
    ----------
    label: :class:`str`
        The label of the text input.
    custom_id: Optional[:class:`str`]
        The custom ID of the text input.
    style: :class:`~.TextInputStyle` = :attr:`~.TextInputStyle.short`
        The style of the text input.
    min_length: Optional[:class:`int`]
        The minimum length in characters of the text input.
    max_length: Optional[:class:`int`]
        The maximum length in characters of the text input.
    required: bool
        Whether the text input is required before submission. Defaults to ``False``.
    default: Optional[:class:`str`]
        The default value of the text input when it is shown to the user.

        Note that this is actually UI-related as opposed to user-end related unlike all other "``default``s".
    placeholder: Optional[:class:`str`]
        The placeholder text of the text input if nothing has been typed in it yet.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    def __init__(
        self,
        *,
        label: str,
        custom_id: str = MISSING,
        style: TextInputStyle = TextInputStyle.short,
        min_length: Optional[int] = MISSING,
        max_length: Optional[int] = MISSING,
        required: bool = False,
        default: str = MISSING,
        placeholder: str = MISSING,
        row: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._provided_custom_id = custom_id is not None
        self._value: Optional[str] = None

        if custom_id is MISSING:
            custom_id = os.urandom(16).hex()

        if min_length is None:
            min_length = 0

        if max_length is None:
            max_length = 4000

        self._underlying = TextInputComponent._raw_construct(
            type=ComponentType.text_input,
            label=label,
            custom_id=custom_id,
            style=style,
            min_length=None if min_length is MISSING else min_length,
            max_length=None if max_length is MISSING else max_length,
            required=required,
            value=default or None,
            placeholder=placeholder or None,
        )
        self._row = row

    @property
    def value(self) -> Optional[str]:
        """The resolved value of this text input, submitted by the user. Only present after submission of the entire parent modal.

        If not present, this will be ``None``.
        """
        return self._value

    @property
    def custom_id(self) -> str:
        """:class:`str`: The custom ID of this text input."""
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('custom_id must be a string.')

        self._underlying.custom_id = value

    @property
    def label(self) -> str:
        """:class:`str`: The label of this text input."""
        return self._underlying.label

    @label.setter
    def label(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('label must be a string.')

        self._underlying.label = value

    @property
    def style(self) -> TextInputStyle:
        """:class:`~.TextInputStyle`: The style of this text input."""
        return self._underlying.style

    @style.setter
    def style(self, value: TextInputStyle) -> None:
        if not isinstance(value, TextInputStyle):
            raise TypeError('style must be a TextInputStyle.')

        self._underlying.style = value

    @property
    def min_length(self) -> Optional[int]:
        """:class:`int`: The minimum length of this text input, or ``None`` if there isn't any set."""
        return self._underlying.min_length

    @min_length.setter
    def min_length(self, value: Optional[int]) -> None:
        if value is not None and not isinstance(value, int):
            raise TypeError('min_length must be an integer or None.')

        if value is None:
            value = 0

        self._underlying.min_length = value

    @property
    def max_length(self) -> Optional[int]:
        """:class:`int`: The maximum length of this text input, or ``None`` if there isn't any set."""
        return self._underlying.max_length

    @max_length.setter
    def max_length(self, value: Optional[int]) -> None:
        if value is not None and not isinstance(value, int):
            raise TypeError('max_length must be an integer or None.')

        if value is None:
            value = 4000

        self._underlying.max_length = value

    @property
    def required(self) -> bool:
        """:class:`bool`: Whether or not this text input is required."""
        return self._underlying.required

    @required.setter
    def required(self, value: bool) -> None:
        self._underlying.required = bool(value)

    @property
    def default(self) -> Optional[str]:
        """:class:`str`: The default value of this text input shown to the user, or ``None`` if there isn't any set."""
        return self._underlying.value

    @default.setter
    def default(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError('default must be a string or None.')

        self._underlying.value = value

    @property
    def placeholder(self) -> Optional[str]:
        """:class:`str`: The placeholder of this text input, or ``None`` if there isn't any set."""
        return self._underlying.placeholder

    @placeholder.setter
    def placeholder(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError('placeholder must be a string or None.')

        self._underlying.placeholder = value

    @property
    def type(self) -> ComponentType:
        return self._underlying.type

    def to_component_dict(self):
        return self._underlying.to_dict()

    def is_dispatchable(self) -> bool:
        return self.custom_id is not None

    def _inject_data(self, data: Dict[str, Any]) -> None:
        self._value = data['value']


@overload
def text_input(
    *,
    label: str,
    custom_id: str = MISSING,
    style: TextInputStyle = TextInputStyle.short,
    min_length: Optional[int] = MISSING,
    max_length: Optional[int] = MISSING,
    required: bool = False,
    default: str = MISSING,
    placeholder: str = MISSING,
    row: Optional[int] = None,
) -> TextInput:
    ...


def text_input(**kwargs) -> TextInput:
    """Defines a "blueprint" for how to construct a new :class:`discord.ui.TextInput` at the top-level of the modal class.

    When defined at the top-level of a subclass of :class:`discord.ui.Modal`, a new instance of a text input will be
    created and added to the modal each time a new instance of the modal in created.

    .. versionadded:: 2.0

    Example ::

        .. code:: python3

            class MyModal(Modal):
                my_input = text_input(label='Here I am!')

    Parameters
    ----------
    label: :class:`str`
        The label of the text input.
    custom_id: Optional[:class:`str`]
        The custom ID of the text input.
    style: :class:`~.TextInputStyle` = :attr:`~.TextInputStyle.short`
        The style of the text input.
    min_length: Optional[:class:`int`]
        The minimum length in characters of the text input.
    max_length: Optional[:class:`int`]
        The maximum length in characters of the text input.
    required: bool
        Whether the text input is required before submission. Defaults to ``False``.
    default: Optional[:class:`str`]
        The default value of the text input when it is shown to the user.

        Note that this is actually UI-related as opposed to user-end related unlike all other "``default``s".
    placeholder: Optional[:class:`str`]
        The placeholder text of the text input if nothing has been typed in it yet.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """
    def callback():
        return TextInput(**kwargs)

    callback.__discord_ui_model_type__ = TextInput
    return callback  # type: ignore
