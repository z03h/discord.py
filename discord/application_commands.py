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

import inspect
import sys

from collections import defaultdict
from dataclasses import dataclass

from .abc import GuildChannel, Messageable, Snowflake
from .channel import TextChannel, _guild_channel_factory
from .enums import ApplicationCommandType, ApplicationCommandOptionType, ChannelType
from .member import Member
from .object import Object
from .role import Role
from .user import User
from .utils import MISSING, resolve_annotation

from typing import (
    Any,
    Dict,
    Final,
    List,
    Literal,
    NamedTuple,
    Sequence,
    Tuple,
    Type,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from .interactions import Interaction
    from .state import ConnectionState

    from .types.interactions import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
        ApplicationCommandInteractionData,
    )

    ApplicationCommandOptionTypeT = Union[
        ApplicationCommandType,
        Literal[
            str,
            int,
            bool,
            User,
            Member,
            Messageable,
            TextChannel,
            GuildChannel,
            Role,
            Object,
            Snowflake,
            float,
        ]
    ]

OPTION_TYPE_MAPPING: Final[Dict[type, ApplicationCommandOptionType]] = {
    str: ApplicationCommandOptionType.string,
    int: ApplicationCommandOptionType.integer,
    bool: ApplicationCommandOptionType.boolean,
    User: ApplicationCommandOptionType.user,
    Member: ApplicationCommandOptionType.user,
    Messageable: ApplicationCommandOptionType.channel,
    TextChannel: ApplicationCommandOptionType.channel,
    GuildChannel: ApplicationCommandOptionType.channel,
    Role: ApplicationCommandOptionType.role,
    Object: ApplicationCommandOptionType.mentionable,
    Snowflake: ApplicationCommandOptionType.mentionable,
    float: ApplicationCommandOptionType.number,
}

__all__ = (
    'ApplicationCommand',
    'ApplicationCommandMeta',
    'ApplicationCommandOption',
    'ApplicationCommandOptionChoice',
    'option',
)


class ApplicationCommandOptionChoice(NamedTuple):
    """Represents a choice of an :class:`.ApplicationCommandOption`.

    Parameters
    ----------
    name: str
        The name of this choice.
    value: Union[str, int, float]
        The value that should be returned when this choice is selected.
    """
    name: str
    value: Union[str, float]  # float is almost identical to Union[int, float]

    def to_dict(self) -> ApplicationCommandOptionChoicePayload:
        return {
            'name': self.name,
            'value': self.value
        }

    def __repr__(self) -> str:
        return f'<ApplicationCommandOptionChoice name={self.name!r} value={self.value!r}>'


@dataclass
class ApplicationCommandOption:
    """Represents an option of an :class:`.ApplicationCommand`.

    These should be constructed via :func:`.option`.
    """
    type: ApplicationCommandOptionType
    name: str
    description: str
    required: bool = False
    choices: List[ApplicationCommandOptionChoice] = MISSING

    def _update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            if not getattr(self, k, False):
                setattr(self, k, v)

    def to_dict(self) -> ApplicationCommandOptionPayload:
        payload = {
            'type': self.type.value,
            'name': self.name,
            'description': self.description,
            'required': bool(self.required),
        }

        if self.choices is not MISSING:
            payload['choices'] = [choice.to_dict() for choice in self.choices]

        return payload

    def __repr__(self) -> str:
        return f'<ApplicationCommandOption type={self.type.name!r} name={self.name!r} required={self.required}>'


def option(
    *,
    type: ApplicationCommandOptionTypeT = MISSING,
    name: str = MISSING,
    description: str,
    required: bool = MISSING,
    optional: bool = MISSING,
    choices: Union[Dict[str, Union[str, float]], Sequence[ApplicationCommandOptionChoice]] = MISSING,
) -> ApplicationCommandOption:
    """Creates an application command option which can be used on :class:`.ApplicationCommand`s.

    All parameters here are keyword-only.

    Parameters
    ----------
    type: Union[:class:`~.ApplicationCommandType`, type]
        The type of this option. Defaults to the annotation given with this option, or ``str``.
    name: str
        The name of this option.
    description: str
        The description of this option. Required.
    required: bool
        Whether or not this option is required. Defaults to ``False``.
    optional: bool
        An inverted alias for ``required``. This cannot be used with ``required``, and vice-versa.
    choices: Union[Dict[str, Union[str, int, float]], Sequence[Union[str, int, float]], Sequence[:class:`.ApplicationCommandOptionChoice`]]
        If specified, only the choices given will be available to be selected by the user.

        Argument should either be a mapping of choice names and their return values,
        A sequence of the possible choices, or a sequence of :class:`.ApplicationCommandOptionChoice`.

    Returns
    -------
    :class:`.ApplicationCommandOption`
    """

    if required is not MISSING and optional is not MISSING:
        raise ValueError('only one of required and optional parameters can be specified.')

    if required is MISSING:
        required = False if optional is MISSING else not optional

    if type is not MISSING and not isinstance(type, ApplicationCommandOptionType):
        try:
            type = OPTION_TYPE_MAPPING[type]
        except KeyError:
            raise ValueError(f'{type!r} is an incompatable option type.')

    if choices is not MISSING:
        if isinstance(choices, dict):
            choices = [
                ApplicationCommandOptionChoice(name=k, value=v)
                for k, v in choices.items()
            ]

        elif isinstances(choices, Sequence):
            if isinstance(choices[0], ApplicationCommandOptionChoice):
                choices = list(choices)
            else:
                choices = [
                    ApplicationCommandOptionChoice(name=str(choice), value=choice)
                    for choice in choices
                ]

    return ApplicationCommandOption(
        type=type,
        name=name.casefold() if name else name,
        description=description,
        required=required,
        choices=choices,
    )


def _get_namespaces(attrs: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    try:
        global_ns = sys.modules[attrs['__module__']].__dict__
    except KeyError:
        global_ns = {}

    frame = inspect.currentframe()
    try:
        if frame is None:
            local_ns = {}
        else:
            parent = frame if frame.f_back is None else frame.f_back
            local_ns = parent.f_locals
    finally:
        del frame

    return local_ns, global_ns


def _resolve_option_annotation(
    option: ApplicationCommandOption,
    annotation: str,
    *,
    args: Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]],
) -> None:
    annotation = resolve_annotation(annotation, *args)

    if not isinstance(annotation, ApplicationCommandOptionType):
        try:
            origin = annotation.__origin__
        except AttributeError:
            pass
        else:
            if origin is Union and annotation.__args__[-1] is type(None):
                annotation = annotation.__args__[0]
                option.required = False

            elif origin is Literal:
                annotation = type(annotation.__args__[0])
                option.choices = [
                    ApplicationCommandOptionChoice(name=str(arg), value=arg)
                    for arg in args
                ]

        try:
            annotation = OPTION_TYPE_MAPPING[annotation]
        except KeyError:
            raise ValueError(f'{annotation!r} is an incompatable option type.')

    option.type = annotation


def _get_application_command_options(
    attrs: Dict[str, Any],
    *,
    option_kwargs: Dict[str, Any] = MISSING
) -> Dict[str, ApplicationCommandOption]:
    if option_kwargs is MISSING:
        option_kwargs = {}

    local_ns, global_ns = _get_namespaces(attrs)
    annotations = attrs.get('__annotations__', {})

    result = {}
    args = global_ns, local_ns, {}

    for name, value in attrs.items():
        if not isinstance(value, ApplicationCommandOption):
            continue

        value._update(**option_kwargs)

        if value.type is MISSING:
            try:
                _resolve_option_annotation(value, annotations[name], args=args)
            except KeyError:
                value.type = ApplicationCommandOptionType.string

        if value.name is MISSING:
            value.name = name.casefold()

        result[name] = value

    if len(option_kwargs):
        for attr, annotation in annotations.items():
            if attr in result:
                return

            result[attr] = res = option(**option_kwargs)
            if res.name is MISSING:
                res.name = attr.casefold()

            if res.type is MISSING:
                _resolve_option_annotation(res, annotation, args=args)

    return result


class ApplicationCommandMeta(type):
    """The metaclass for defining an application command.

    Anything documented here can be used directly on classes that use this metaclass.

    Parameters
    ----------
    type: :class:`~.ApplicationCommandType`
        The type of command this is. Defaults to ``chat_input`` (slash commands).
    name: str
        The name of this application command. Defaults to the class name.
    description: str
        The description of this command. Must be present here or as a doc-string.
    parent: Type[:class:`.ApplicationCommand`]
        The parent command of this command. Note that parent commands can't have callbacks.
    default_permission: bool
        Whether or not this command is enabled by default when added to a guild.
        Defaults to ``True``
    option_kwargs: Dict[str, Any]:
        Default kwargs to pass in for each option.
    """

    if TYPE_CHECKING:
        __application_command_type__: ApplicationCommandType
        __application_command_name__: str
        __application_command_description__: str
        __application_command_default_permission__: bool
        __application_command_options__: Dict[str, ApplicationCommandOption]
        __application_command_parent__: ApplicationCommandMeta
        __application_command_children__: Dict[str, ApplicationCommand]

    def __new__(
        mcs: Type[ApplicationCommandMeta],
        cls_name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
        *,
        type: ApplicationCommandType = ApplicationCommandType.chat_input,
        name: str = MISSING,
        description: str = MISSING,
        parent: ApplicationCommandMeta = MISSING,
        default_permission: bool = True,
        option_kwargs: Dict[str, Any] = MISSING,
        **kwargs,
    ) -> ApplicationCommandMeta:
        if not isinstance(type, ApplicationCommandType):
            raise TypeError('application command types must be an ApplicationCommandType.')

        if 'callback' in attrs and not callable(attrs['callback']):
            raise TypeError('application command callback must be callable.')

        if name is MISSING:
            name = cls_name

        if description is MISSING:
            try:
                description = inspect.cleandoc(attrs['__doc__'])
            except KeyError:
                raise TypeError('application commands must have a description.')

        attrs.update(
            __application_command_type__=type,
            __application_command_name__=name.casefold(),
            __application_command_description__=description,
            __application_command_parent__=parent,
            __application_command_default_permission__=default_permission,
        )

        attrs['__application_command_options__'] = _get_application_command_options(attrs, option_kwargs=option_kwargs)
        attrs['__application_command_children__'] = children = {}

        cls = super().__new__(mcs, cls_name, bases, attrs, **kwargs)

        if parent is not MISSING:
            parent.__application_command_children__[cls.__application_command_name__] = cls

        for name, value in attrs.items():
            if isinstance(value, mcs):
                children[value.__application_command_name__] = value
                value.__application_command_parent__ = cls

        return cls

    def to_option_dict(cls) -> ApplicationCommandOptionPayload:
        payload = {
            'name': cls.__application_command_name__,
            'description': cls.__application_command_description__,
            'options': [],
        }

        if len(children := cls.__application_command_children__):
            option_type = ApplicationCommandOptionType.subcommand_group
            payload['options'] += [command.to_option_dict() for command in children.values()]
        else:
            option_type = ApplicationCommandOptionType.subcommand

        if len(options := cls.__application_command_options__):
            payload['options'] += [option.to_dict() for option in options.values()]

        if not payload['options']:
            del payload['options']

        payload['type'] = option_type.value
        return payload

    def to_dict(cls) -> ApplicationCommandPayload:
        payload = {
            'type': cls.__application_command_type__.value,
            'name': cls.__application_command_name__,
            'default_permission': cls.__application_command_default_permission__,
            'options': [],
        }

        if cls.__application_command_type__ is ApplicationCommandType.chat_input:
            payload['description'] = cls.__application_command_description__

        if len(children := cls.__application_command_children__):
            payload['options'] += [command.to_option_dict() for command in children.values()]

        if len(options := cls.__application_command_options__):
            payload['options'] += [option.to_dict() for option in options.values()]

        if not payload['options']:
            del payload['options']

        return payload


class ApplicationCommand(metaclass=ApplicationCommandMeta):
    """Represents an application command."""

    async def command_check(self, interaction: Interaction) -> bool:
        """|coro|

        The check for when this command is invoked.

        If an error is raised, or this check fails, the callback will not be ran.
        You should respond to the interaction here to prevent client-side errors.

        Parameters
        ----------
        interaction: :class:`~.Interaction`
            The interaction to check.

        Returns
        -------
        bool
            Whether or not this check succeeded or not.
        """
        return True

    async def command_error(self, interaction: Interaction, error: Exception) -> None:
        """|coro|

        The error handler for when an error is raised either during the :meth:`command_check`
        or during the :meth:`callback`.

        If an error is raised here, :func:`on_application_command_error` will be dispatched.

        Parameters
        ----------
        interaction: :class:`~.Interaction`
            The interaction that caused this error.
        error: :exc:`Exception`
            The exception that was raised.
        """
        raise error

    async def callback(self, interaction: Interaction) -> None:
        """|coro|

        The callback for when this command is invoked.

        Parameters
        ----------
        interaction: :class:`~.Interaction`
            The interaction created when this command was invoked.
        """


class ApplicationCommandStore:
    def __init__(self, state: ConnectionState) -> None:
        self.state: ConnectionState = state
        self.commands: Dict[int, ApplicationCommandMeta] = {}

    def store_command(self, id: int, command: ApplicationCommandMeta) -> None:
        self.commands[id] = command

    async def _handle_error(
        self,
        command: ApplicationCommand,
        interaction: discord.Interaction,
        error: Exception
    ) -> None:
        try:
            await command.command_error(interaction, error)
        except Exception as exc:
            self.state.dispatch('application_command_error', interaction, exc)

    async def invoke(self, command: ApplicationCommand, interaction: discord.Interaction) -> None:
        self.state.dispatch('application_command', interaction)

        try:
            can_run = await command.command_check(interaction)
        except Exception as exc:
            return await self._handle_error(command, interaction, exc)

        if can_run:
            try:
                await command.callback(interaction)
            except Exception as exc:
                return await self._handle_error(command, interaction, exc)
            else:
                self.state.dispatch('application_command_completion', interaction)

    def _parse_options(
        self,
        *,
        data: ApplicationCommandInteractionData,
        command: ApplicationCommandMeta,
        guild_id: int,
    ) -> ApplicationCommand:
        options = data.get('options', [])
        resolved = data.get('resolved', {})
        to_parse = options

        # In the first iteration, sanitize the command and options.
        for option in options:
            if option['type'] < 3:
                command = command.__application_command_children__[option['name']]
                to_parse = option['options']

                if option['type'] == 2:
                    command = command.__application_command_children__[to_parse[0]['name']]
                    to_parse = to_parse[0]['options']

                break

        command = command()

        for key in command.__class__.__application_command_options__:
            setattr(command, key, None)  # For options that were not given

        maybe_guild = self.state._get_guild(guild_id)

        for option in to_parse:
            value = option['value']
            type = option['type']

            if type == 6:
                user_data = member_data = None

                if value in resolved['users']:
                    user_data = resolved['users'][value]

                if value in resolved['members']:
                    member_data = resolved['members'][value]

                if user_data and member_data:
                    member_data['user'] = user_data

                if member_data is not None and maybe_guild:
                    value = Member(data=member_data, state=self.state, guild=maybe_guild)
                else:
                    value = User(data=user_data, state=self.state)

            elif type == 7:
                # Prefer from cache
                cached = self.state.get_channel(int(value))
                if cached is None:
                    channel_data = defaultdict(lambda: None)
                    channel_data.update(resolved['channels'][value])
                    factory, _ = _guild_channel_factory(channel_data['type'])
                    value = factory(state=self.state, data=channel_data, guild=maybe_guild)
                else:
                    value = cached

            elif type == 8:
                # Here we prefer from payload instead, as the data
                # is more up to date.
                role_data = resolved['roles'][value]
                value = Role(state=self.state, data=role_data, guild=maybe_guild)

            elif type == 9:
                value = Object(id=int(value))

            for k, v in command.__class__.__application_command_options__.items():
                v: ApplicationCommandOption
                if v.name == option['name']:
                    setattr(command, k, value)
                    break

        return command

    def dispatch(self, data: ApplicationCommandInteractionData, interaction: discord.Interaction) -> None:
        try:
            command_factory = self.commands[int(data['id'])]
        except KeyError:
            return

        command = self._parse_options(data=data, command=command_factory, guild_id=interaction.guild_id)
        self.state.loop.create_task(
            self.invoke(command, interaction), name=f'discord-application-commands-dispatch-{interaction.id}'
        )
