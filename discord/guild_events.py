"""
The MIT License (MIT)

Copyright (c) 2022-present z03h

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

from typing import TYPE_CHECKING, Optional, Union
from .iterators import GuildEventUserIterator
from .channel import VoiceChannel, StageChannel
from .errors import InvalidArgument
from .object import Object
import datetime

from . import utils
from .mixins import Hashable
from .user import User
from .enums import (
    GuildEventStatus,
    GuildEventLocationType,
    GuildEventPrivacyLevel,
    try_enum,
)

MISSING = utils.MISSING

__all__ = ('GuildEvent',)

if TYPE_CHECKING:
    from .guild import Guild
    from .abc import Snowflake
    from .iterators import AsyncIterator
    from .types.guild_events import GuildEvent as GuildEventPayload
    from .state import ConnectionState


class GuildEvent(Hashable):
    """Represents a Discord Guild Scheduled Event.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two events are equal.

        .. describe:: x != y

            Checks if two events are not equal.

        .. describe:: hash(x)

            Returns the event's hash.

        .. describe:: str(x)

            Returns the event's name.

    Attributes
    ----------
    name: :class:`str`
        The name of the  event.
    description: Optional[:class:`str`]
        The description of the  event.
    start_time: :class:`datetime.datetime`
        The time when the event will start
    end_time: Optional[:class:`datetime.datetime`]
        The time when the event is supposed to end.
    channel_id: Optional[:class:`int`]
        ID of the channel where event is scheduled to take place.
        ``None`` if type is External.
    status: :class:`GuildEventStatus`
        The status of the event.
    location_type: :class:`GuildEventLocationType`
        The type of location for where this event is scheduled to take place.
    creator_id: Optional[:class:`int`]
        The ID of the user who created the event.
        Will be  ``None`` for events created before October 25th, 2021.
    creator: Optional[Union[:class:`Member`, :class:`User`]]
        The member or user who created the event.
        Will be  ``None`` for events created before October 25th, 2021.
    privacy_level: :class:`GuildEventPrivacyLevel`
        The privacy level of the event.
    user_count: optional[:class:`int`]
        The number of users interested in this event.

        .. note::

            This will only be available if event is fetch with :meth:`Guild.fetch_event`
            or :meth:`Guild.fetch_events` and ``with_user_count`` set to ``True``.

    guild: :class:`Guild`
        The guild where the event is scheduled.
    """
    __slots__ = (
        '_state',
        'guild',
        'id',
        'name',
        'description',
        'privacy_level',
        'location_type',
        'status',
        'creator_id',
        'creator',
        'start_time',
        'end_time',
        'channel_id',
        '_location',
        'user_count',
    )

    def __init__(self, *, guild: Guild, data: GuildEventPayload, state: ConnectionState):
        self._state = state
        self._update(guild, data, state)

    def _update(self, guild, data, state):
        self.guild = guild

        self.id = utils._get_as_snowflake(data, 'id')
        self.name = data['name']
        self.description = data.get('description')

        self.privacy_level = try_enum(GuildEventPrivacyLevel, data['privacy_level'])
        self.location_type = try_enum(GuildEventLocationType, data['entity_type'])
        self.status = try_enum(GuildEventStatus, data['status'])
        self.user_count = data.get('user_count', 0)

        self.creator_id = utils._get_as_snowflake(data, 'creator_id')
        self.creator = None
        # safeguard against old events maybe not having creator_id or creator
        if self.creator_id:
            try:
                self.creator = guild.get_member(self.creator_id) or state.get_user(self.creator_id)
            except AttributeError:
                self.creator = state.get_user(self.creator_id)

        if not self.creator:
            creator_data = data.get('creator')
            if creator_data:
                self.creator = User(state=state, data=creator_data)

        self.start_time = utils.parse_time(data['scheduled_start_time'])
        self.end_time = utils.parse_time(data['scheduled_end_time'])

        self.channel_id = utils._get_as_snowflake(data, 'channel_id')
        metadata = data.get('event_metadata')
        self.parse_metadata(metadata)

    def parse_metadata(self, metadata):
        if not metadata:
            self._location = None
        else:
            self._location = metadata.get('location')

    def __repr__(self):
        return f'<GuildEvent id={self.id} name={self.name} location={self.location} status={self.status} guild={self.guild}>'

    def __str__(self):
        return self.name

    @property
    def location(self) -> Union[VoiceChannel, StageChannel, str]:
        """The location of this event"""
        return self._location or self.channel

    @property
    def channel(self) -> Optional[Union[VoiceChannel, StageChannel]]:
        """The channel where this event is scheduled to take place.
        Can be ``None`` if location type is external.
        """
        if self.channel_id:
            return self.guild.get_channel(self.channel_id) or Object(id=self.channel_id)
        return None

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the events's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def duration(self):
        """How long the event will last.
        Can be ``None`` if missing :attr:`GuildEvent.end_time`
        """
        if not self.start_time or not self.end_time:
            return None
        return self.end_time - self.start_time

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        status: GuildEventStatus = MISSING,
        location: Union[StageChannel, VoiceChannel, str] = MISSING,
        start_time: datetime.datetime = MISSING,
        end_time: datetime.datetime = MISSING,
        privacy_level: GuildEventPrivacyLevel = MISSING,
        reason: Optional[str] = None
    ):
        """|coro|

        Edits the event.

        All parameters are optional unless ``location.type`` is
        :attr:`GuildEventLocationType.external`, then ``end_time``
        is required.

        Will return a new :class:`.GuildEvent` object if applicable.

        Parameters
        -----------
        name: :class:`str`
            The new name of the event.
        description: :class:`str`
            The new description of the event.
        location: Union[:class:`VoiceChannel`, :class:`StageChannel`, :class:`str`]
            The location of the event.
        status: :class:`GuildEventStatus`
            The status of the event.
        start_time: :class:`datetime.datetime`
            The new starting time for the event.
        end_time: :class:`datetime.datetime`
            The new ending time of the event.
        privacy_level: :class:`GuildEventPrivacyLevel`
            The privacy level of the event.
        reason: Optional[:class:`str`]
            The reason to show in the audit log.

        Raises
        -------
        InvalidArgument
            Event location type is external and doesn't have an end time set.
        Forbidden
            You do not have the Manage Events permission.
        HTTPException
            The operation failed.

        Returns
        --------
        :class:`.GuildEvent`
            The updated event.
        """
        payload = {}

        if name is not MISSING:
            payload["name"] = name

        if description is not MISSING:
            payload["description"] = description

        if status is not MISSING:
            payload["status"] = int(status)

        if privacy_level is not MISSING:
            payload["privacy_level"] = int(privacy_level)

        if location is not MISSING:
            if isinstance(location, str):
                # external
                payload['entity_metadata'] = {'location': location}
                payload['channel_id'] = None
                payload['entity_type'] = int(GuildEventLocationType.external)
            else:
                payload['entity_metadata'] = None
                try:
                    payload['channel_id'] = location.id
                except AttributeError:
                    raise TypeError('location must be a VoiceChannel, StageChannel, or str.')

                if isinstance(location, VoiceChannel):
                    payload['entity_type'] = int(GuildEventLocationType.voice)
                elif isinstance(location, StageChannel):
                    payload['entity_type'] = int(GuildEventLocationType.stage)
                else:
                    raise TypeError('location must be a VoiceChannel, StageChannel, or str.')

        if start_time is not MISSING:
            payload["scheduled_start_time"] = start_time.isoformat()

        if end_time is not MISSING:
            payload["scheduled_end_time"] = end_time.isoformat() if end_time is not None else end_time
        if isinstance(location, str) and not self.end_time and not end_time:
            raise InvalidArgument('end_time must be provided for events with external location type')

        if payload:
            data = await self._state.http.edit_guild_event(self.guild.id, self.id, reason=reason, **payload)
            return GuildEvent(data=data, guild=self.guild, state=self._state)

        return self

    async def delete(self, *, reason: Optional[str] = None):
        """|coro|

        Cancels and deletes this event.

        Parameters
        -----------
        reason: Optional[str]
            The reason for deletion.

        Raises
        -------
        Forbidden
            You do not have the Manage Events permission.
        HTTPException
            The operation failed.

        """
        await self._state.http.delete_guild_event(self.guild.id, self.id, reason=reason)

    def users(
        self,
        *,
        limit: Optional[int] = None,
        with_member: bool = False,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
        after: Optional[Union[Snowflake, datetime.datetime]] = None,
    ) -> AsyncIterator:
        """Returns an :class:`AsyncIterator` representing the users or members subscribed to the event.

        Examples
        ---------
        Usage ::

            async for user in event.users(limit=100):
                print(user.name)

        Flattening all users as members into a list: ::

            users = await event.users(limit=None, with_member=True).flatten()

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The maximum number of results to return.
        with_member: Optional[:class:`bool`]
            Whether to fetch :class:`Member` objects instead of user objects.
            There may still be :class:`User` objects.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieves users before this date or object. If a datetime is provided,
            it is recommended to use a UTC aware datetime. If the datetime is naive,
            it is assumed to be local time.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieves users after this date or object. If a datetime is provided,
            it is recommended to use a UTC aware datetime. If the datetime is naive,
            it is assumed to be local time.

        Raises
        -------
        ~discord.HTTPException
            Fetching the subscribed users failed.

        Yields
        -------
        Union[:class:`User`, :class:`Member`]
            The subscribed user or member.
        """

        return GuildEventUserIterator(event=self, limit=limit, with_member=with_member, before=before, after=after)
