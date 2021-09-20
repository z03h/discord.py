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

from typing import List, Type, TypeVar, TYPE_CHECKING, Sequence, Union

from .partial_emoji import PartialEmoji
from .utils import _get_as_snowflake, MISSING

if TYPE_CHECKING:
    from .abc import Snowflake
    from .emoji import Emoji
    from .guild import Guild
    from .state import ConnectionState

    from .types.welcome_screen import (
        WelcomeScreen as WelcomeScreenPayload,
        WelcomeScreenChannel as WelcomeChannelPayload,
    )

    EmojiT = Union[Emoji, PartialEmoji, str, None]
    WelcomeChannelT = TypeVar('WelcomeChannelT', bound='WelcomeChannel')

__all__ = (
    'WelcomeChannel',
    'WelcomeScreen',
    'PartialWelcomeScreen',
)


class WelcomeChannel:
    """Represents a channel for a :class:`WelcomeScreen`.

    .. versionadded:: 2.0

    Parameters
    ----------
    channel: :class:`abc.GuildChannel`
        The actual channel this will direct to.
    description: str
        The description of this welcome channel.
    emoji: Optional[Union[:class:`Emoji`, :class:`PartialEmoji`, str]]
        The emoji that will be displayed next to the channel and description.
    """

    def __init__(self, *, channel: Snowflake, description: str, emoji: EmojiT = None) -> None:
        self.channel: Snowflake = channel
        self.description: str = description
        self.emoji: EmojiT = emoji

    def __repr__(self) -> str:
        return f'<WelcomeChannel channel={self.channel!r} description={self.description!r} emoji={self.emoji!r}>'

    @classmethod
    def _from_data(cls: Type[WelcomeChannelT], *, data: WelcomeChannelPayload, guild: Guild) -> WelcomeChannelT:
        channel = guild.get_channel(_get_as_snowflake(data, 'channel_id'))
        emoji = PartialEmoji(name=data['emoji_name'], id=_get_as_snowflake(data, 'emoji_id'))

        return cls(channel=channel, description=data['description'], emoji=emoji)

    def to_dict(self) -> WelcomeChannelPayload:
        payload = {
            'channel_id': str(self.channel.id),
            'description': self.description,
            'emoji_name': None,
            'emoji_id': None,
        }

        if isinstance(emoji := self.emoji, str):
            payload['emoji_name'] = emoji

        elif isinstance(emoji, (PartialEmoji, Emoji)):
            payload['emoji_name'] = emoji.name
            payload['emoji_id'] = emoji.id

        return payload


class _WelcomeScreenMixin:
    _state: ConnectionState
    guild: Guild

    @property
    def enabled(self) -> bool:
        """bool: Whether or not the welcome screen is enabled."""
        return 'WELCOME_SCREEN_ENABLED' in self.guild.features

    async def edit(
        self,
        *,
        description: str = MISSING,
        channels: Sequence[WelcomeChannel] = MISSING,
        enabled: bool = MISSING,
        reason: str = None,
    ) -> WelcomeScreen:
        """|coro|

        Edits the welcome screen.

        You must have the :attr:`~Permissions.manage_guild` permission
        to edit the welcome screen.

        Parameters
        ----------
        description: str
            The new description of the welcome screen.
        channels: Sequence[:class:`WelcomeChannel`]
            A sequence of the new welcome channels.
        enabled: bool
            Whether or not this welcome screen should be enabled.
            Setting this to ``False`` will disable the welcome screen.
        reason: str
            The reason on modifying the welcome screen. This will appear in the audit logs.

        Raises
        ------
        HTTPException
            Editing the welcome screen failed.
        Forbidden
            You don't have permissions to edit the welcome screen.
        """

        payload = {}

        if description is not MISSING:
            payload['description'] = description

        if channels is not MISSING:
            payload['welcome_channels'] = [channel.to_dict() for channel in channels]

        if enabled is not MISSING:
            payload['enabled'] = bool(enabled)

        data = await self._state.http.edit_welcome_screen(guild_id=self.guild.id, payload=payload, reason=reason)
        return WelcomeScreen(data=data, guild=self.guild, state=self._state)


class WelcomeScreen(_WelcomeScreenMixin):
    """Represents a guild's welcome screen.

    .. versionadded:: 2.0

    Attributes
    ----------
    description: str
        The server description shown in the welcome screen.
    channels: List[:class:`WelcomeChannel`]
        A list of the channels shown on the welcome screen.
    guild: :class:`Guild`
        The guild this welcome screen belongs to.
    """

    def __init__(self, *, data: WelcomeScreenPayload, guild: Guild, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<WelcomeScreen enabled={self.enabled} description={self.description!r}>'

    def _from_data(self, data: WelcomeScreenPayload) -> None:
        self.channels: List[WelcomeChannel] = [
            WelcomeChannel._from_data(data=channel, guild=self.guild)
            for channel in data['welcome_channels']
        ]
        self.description: str = data['description']


class PartialWelcomeScreen(_WelcomeScreenMixin):
    """Represents a user-constructed welcome screen with minimal fields.

    This is useful for editing a guild's welcome screen without actually fetching it.

    .. versionadded:: 2.0

    Parameters
    ----------
    guild: :class:`Guild`
        The guild this welcome screen should belong to.
    """

    def __init__(self, guild: Guild) -> None:
        self._state: ConnectionState = guild._state
        self.guild: Guild = guild

    def __repr__(self) -> str:
        return f'<WelcomeScreen enabled={self.enabled}>'
