#!/usr/bin/env python3.8
import asyncio
import datetime
import typing

import discord
from discord.ext import commands


class SnipedMessage:
    """A special class for sniped messages, using slots to keep the memory usage to a minimum."""

    __slots__ = ("embed", "time_modified")

    def __init__(self, embed: discord.Embed):
        self.embed = embed
        self.time_modified = datetime.datetime.utcnow()


class UsableIDConverter(commands.IDConverter):
    """The internal ID converter, but usable."""

    async def convert(self, ctx: commands.Context, argument: str):
        match = self._get_id_match(argument)
        try:
            return int(match.group(1))
        except:
            raise commands.MessageNotFound(argument)


class SetAsyncQueue(asyncio.Queue):
    """A special type of async queue that uses a set instead of a queue.
    Useful when we don't want duplicates."""

    def _init(self, maxsize):
        self._queue = set()
        self._queuecopy = set()

    def _get(self):
        return self._queue.pop()

    def _put(self, item):
        if not item in self._queuecopy:
            self._queue.add(item)
            self._queuecopy.add(item)

    def remove_from_copy(self, item):
        self._queuecopy.discard(item)


class TimeDurationConverter(commands.Converter):
    """Converts a string to a time duration.
    Works very similarly to YAGPDB's time duration converter.
    In fact, entering in a time duration that works for YAG will probably work here."""

    convert_dict = {
        "s": 1,
        "second": 1,
        "seconds": 1,
        "m": 60,  # s * 60
        "minute": 60,
        "minutes": 60,
        "h": 3600,  # m * 60
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
        time_span = 0  # will be how long the duration is, in seconds

        value_entry = []
        format_entry = []

        # we want to effectively ignore spaces and not want to worry about caps here
        formatted_arg = argument.replace(" ", "").lower()

        for chara in formatted_arg:
            if (
                chara.isdigit() or chara == "."
            ):  # if a character is a digit or a '.' - aka if the character is part of a number
                if (
                    format_entry
                ):  # if this already exists, that means there was a format before the current number
                    # basically, this number represents the start of a new part of the duration, and we need to add in the old one
                    # format entry should have the format of the previous part, so store that
                    time_format_list.append("".join(format_entry))
                    format_entry.clear()

                value_entry.append(chara)  # slowly build up our number

            else:
                if (
                    value_entry
                ):  # if this already exists, that means we just came off a number
                    # so we need to store that number and prepare to get the measurement unit after it
                    time_value_list.append(
                        float("".join(value_entry))
                    )  # numbers are floats
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

        for time_value, time_format in zip(time_value_list, time_format_list):
            # build up the time span by going through each seperate value and format
            # and processing it into seconds, and then adding it to the total seconds
            # the duration represents
            time_span += self.to_seconds(time_value, time_format)

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


class WizardManager:
    """A class that allows you to make a wizard of sorts, allowing a more intuitive way of getting multiple inputs from a user."""

    def __init__(
        self,
        embed_title: str,
        timeout: float,
        final_text: str,
        color=discord.Colour(0x4378FC),
    ):
        self.embed_title = embed_title
        self.timeout = timeout
        self.final_text = final_text
        self.color = color

        self.questions = []
        self.ori_mes: typing.Optional[discord.Message] = None

    def add_question(self, question: str, converter, action):
        self.questions.append((question, converter, action))

    async def run(self, ctx: commands.Context):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        wizard_embed = discord.Embed(title=self.embed_title, colour=self.color)
        wizard_embed.set_author(
            name=f"{ctx.bot.user.name}",
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png', size=128))}",
        )
        wizard_embed.set_footer(
            text="If you wish to stop this setup at any time, just type in 'exit'."
        )

        for question in self.questions:
            wizard_embed.description = question[0]

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
                    question[1], ctx, reply.content
                )
            except:
                wizard_embed.description = "Invalid input. Exiting..."
                wizard_embed.set_footer(text=discord.Embed.Empty)
                await self.ori_mes.edit(embed=wizard_embed)
                return

            await discord.utils.maybe_coroutine(question[2], ctx, converted)

        wizard_embed.description = self.final_text
        wizard_embed.set_footer(text=discord.Embed.Empty)
        await self.ori_mes.edit(embed=wizard_embed)
