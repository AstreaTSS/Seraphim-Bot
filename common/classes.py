#!/usr/bin/env python3.8
import asyncio
import datetime
import typing

import attr
import discord
from discord.ext import commands

import common.utils as utils

_T = typing.TypeVar("_T")


@attr.s(slots=True)
class SnipedMessage:
    """A special class for sniped messages."""

    embed: discord.Embed
    time_modified: datetime.datetime = attr.ib(factory=discord.utils.utcnow)


if typing.TYPE_CHECKING:

    class SetAsyncQueue(asyncio.Queue[_T]):
        ...

    class SetUpdateAsyncQueue(SetAsyncQueue[_T]):
        ...

    class SetNoReaddAsyncQueue(asyncio.Queue[_T]):
        ...


else:

    class SetAsyncQueue(asyncio.Queue):
        """A special type of async queue that uses a set instead of a list."""

        def _init(self, maxsize):
            self._queue = set()

        def _get(self):
            return self._queue.pop()

        def _put(self, item):
            self._queue.add(item)

    class SetUpdateAsyncQueue(SetAsyncQueue):
        """A special type of async queue that uses a set instead of a list.
        Also updates instead of discards entries if it encounters a duplicate."""

        def _put(self, item) -> None:
            # admittedly, a hack, but a hack that's efficient
            self._queue.discard(item)
            self._queue.add(item)

    class SetNoReaddAsyncQueue(asyncio.Queue):
        """A special type of async queue that uses a set instead of a list.
        Also ensures entries cannot be re-added (at the expense of using more memory)."""

        def _init(self, maxsize):
            self._queue = set()
            self._queuecopy = set()

        def _get(self):
            return self._queue.pop()

        def _put(self, item):
            if item not in self._queuecopy:
                self._queue.add(item)
                self._queuecopy.add(item)

        def remove_from_copy(self, item):
            self._queuecopy.discard(item)

        def clear_memory(self):
            self._queuecopy.clear()


class PowerofTwoConverter(commands.Converter[int]):
    """A converter to check if the argument provided is a valid Discord power of 2."""

    def convert(self, ctx: commands.Context, argument: str):
        if not (argument.isdigit() and discord.utils.valid_icon_size(int(argument))):
            raise commands.BadArgument(
                f"{argument} is not a power of 2 between 16 and 4096."
            )
        return int(argument)


class TimeDurationConverter(commands.Converter[datetime.timedelta]):
    """Converts a string to a time duration.
    Works very similarly to YAGPDB's time duration converter.
    In fact, entering in a time duration that works for YAG will probably work here."""

    convert_dict = {
        "s": 1,
        "sec": 1,
        "secs": 1,
        "second": 1,
        "seconds": 1,
        "m": 60,  # s * 60
        "min": 60,
        "mins": 60,
        "minute": 60,
        "minutes": 60,
        "h": 3600,  # m * 60
        "hr": 3600,
        "hrs": 3600,
        "hour": 3600,
        "hours": 3600,
        "d": 86400,  # h * 24
        "day": 86400,
        "days": 86400,
        "mo": 2592000,  # d * 30
        "month": 2592000,
        "months": 2592000,
        "y": 31536000,  # d * 365
        "year": 31536000,
        "years": 31536000,
    }

    def to_seconds(self, time_value, time_prefix):
        try:
            return self.convert_dict[time_prefix] * time_value
        except KeyError:
            raise commands.BadArgument(f"{time_prefix} is not a valid time prefix.")

    async def convert(self, ctx, argument: str):
        time_value_list = []  # will be list of all numbers, ie the '60' in '60d'
        time_format_list = []  # will be list of all formats, ie the 'd' in '60d'
        value_entry = []
        format_entry = []

        # we want to effectively ignore spaces and not want to worry about caps here
        formatted_arg = argument.replace(" ", "").lower()

        for chara in formatted_arg:
            if (
                chara.isdigit() or chara == "."
            ):  # if a character is a digit or a '.' - aka if the character is part of a number

                # if the below already exists, that means there was a format before the current number
                if format_entry:
                    # basically, this number represents the start of a new part of the duration, and we need to add in the old one
                    # format entry should have the format of the previous part, so store that
                    time_format_list.append("".join(format_entry))
                    format_entry.clear()

                value_entry.append(chara)  # slowly build up our number

            else:
                if value_entry:
                    # if this already exists, that means we just came off a number
                    # so we need to store that number and prepare to get the measurement unit after it
                    try:
                        time_value_list.append(
                            float("".join(value_entry))
                        )  # numbers are floats
                    except ValueError:  # because you could do ".s"
                        raise commands.BadArgument(
                            f"Argument {argument} is not a valid time duration."
                        )
                    value_entry.clear()

                format_entry.append(chara)  # slowly build up our unit

        # if there any values still not added to either list after the string is over, add them to the lists
        # we would miss out on things like the last unit or the last number if we didn't do this
        if value_entry:
            time_value_list.append(float("".join(value_entry)))
        if format_entry:
            time_format_list.append("".join(format_entry))

        # if the list of units/formats is one less than the list of numbers/values
        if len(time_format_list) + 1 == len(time_value_list):
            time_format_list.append(
                "m"
            )  # yag assumes a number with no digit is a minute, so we do too

        if (
            not time_format_list
            or not time_value_list
            or len(time_format_list) != len(time_value_list)
        ):  # if either list is empty and has no units/numbers or if the two are not equal,
            # we know this cannot be correct with an actual duration, so we error out
            raise commands.BadArgument(
                f"Argument {argument} is not a valid time duration."
            )

        time_span = sum(
            self.to_seconds(time_value, time_format)
            for time_value, time_format in zip(time_value_list, time_format_list)
        )

        # timedeltas are generally useful for this type of stuff
        return datetime.timedelta(seconds=time_span)


class ValidChannelConverter(commands.TextChannelConverter):
    """The text channel converter, but we do a few checks to make sure we can do what we need to do in the channel."""

    async def convert(self, ctx: commands.Context, argument: str):
        chan = await super().convert(ctx, argument)
        perms = chan.permissions_for(ctx.guild.me)

        if not perms.read_messages:  # technically pointless, but who knows
            raise commands.BadArgument(f"Cannot read messages in {chan.name}.")
        elif not perms.read_message_history:
            raise commands.BadArgument(f"Cannot read message history in {chan.name}.")
        elif not perms.send_messages:
            raise commands.BadArgument(f"Cannot send messages in {chan.name}.")
        elif not perms.embed_links:
            raise commands.BadArgument(f"Cannot send embeds in {chan.name}.")

        return chan


@attr.s(slots=True)
class WizardQuestion:
    question: str = attr.ib()
    converter: typing.Callable = attr.ib()
    action: typing.Callable = attr.ib()


@attr.s
class WizardManager:
    """A class that allows you to make a wizard of sorts, allowing a more intuitive way of getting multiple inputs from a user."""

    embed_title: str = attr.ib()
    final_text: str = attr.ib()
    color: discord.Color = attr.ib(default=discord.Color(0x4378FC))
    timeout: float = attr.ib(default=120)
    pass_self: bool = attr.ib(default=False)

    questions: typing.List[WizardQuestion] = attr.ib(factory=list, init=False)
    ori_mes: typing.Optional[discord.Message] = attr.ib(default=None, init=False)

    def add_question(
        self, question: str, converter: typing.Callable, action: typing.Callable
    ):
        self.questions.append(WizardQuestion(question, converter, action))

    async def run(self, ctx: commands.Context):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        wizard_embed = discord.Embed(title=self.embed_title, colour=self.color)
        wizard_embed.set_author(
            name=f"{ctx.bot.user.name}",
            icon_url=utils.get_icon_url(ctx.guild.me.display_avatar),
        )
        wizard_embed.set_footer(
            text="If you wish to stop this setup at any time, just type in 'exit'."
        )

        for question in self.questions:
            wizard_embed.description = question.question

            if not self.ori_mes:
                self.ori_mes = await ctx.reply(embed=wizard_embed)
            else:
                await self.ori_mes.edit(embed=wizard_embed)

            try:
                reply = await ctx.bot.wait_for(
                    "message", check=check, timeout=self.timeout
                )
            except asyncio.TimeoutError:
                wizard_embed.description = "Failed to reply. Exiting..."
                wizard_embed.set_footer(text=discord.Embed.Empty)
                await self.ori_mes.edit(embed=wizard_embed)
                return
            else:
                if reply.content.lower() == "exit":
                    wizard_embed.description = "Exiting..."
                    wizard_embed.set_footer(text=discord.Embed.Empty)
                    await self.ori_mes.edit(embed=wizard_embed)
                    return

            try:
                converted = await discord.utils.maybe_coroutine(
                    question.converter, ctx, reply.content
                )
            except Exception as e:  # base exceptions really shouldn't be caught
                wizard_embed.description = (
                    f"Invalid input. Exiting...\n\nError: {str(e)}"
                )
                wizard_embed.set_footer(text=discord.Embed.Empty)
                await self.ori_mes.edit(embed=wizard_embed)
                return

            if not self.pass_self:
                await discord.utils.maybe_coroutine(question.action, ctx, converted)
            else:
                await discord.utils.maybe_coroutine(
                    question.action, ctx, converted, self
                )

        wizard_embed.description = self.final_text
        wizard_embed.set_footer(text=discord.Embed.Empty)
        await self.ori_mes.edit(embed=wizard_embed)
