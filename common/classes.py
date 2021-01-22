#!/usr/bin/env python3.7
from discord.ext import commands
import discord, re, datetime
import asyncio, typing

class SnipedMessage():
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

class TimeDurationConverter(commands.Converter):
    """Converts a string to a time duration.
    Works very similarly to YAGPDB's time duration converter."""

    convert_dict = {
        "s": 1,
        "second": 1,
        "seconds": 1,

        "m": 60, # s * 60
        "minute": 60,
        "minutes": 60,

        "h": 3600, # m * 60
        "hour": 3600,
        "hours": 3600,

        "d": 86400, # h * 24
        "day": 86400,
        "days": 86400,

        "mo": 2592000, # d * 30
        "month": 2592000,
        "months": 2592000,

        "y": 31536000, # d * 365
        "year": 31536000,
        "years": 31536000
    }
    regex = re.compile(r"([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[eE]([+-]?\d+))?") # splits character and number

    def to_seconds(self, time_value, time_prefix):
        try:
            return self.convert_dict[time_prefix] * time_value
        except KeyError:
            raise commands.BadArgument(f"{time_prefix} is not a valid time prefix.")

    async def convert(self, ctx, argument):
        time_value_list = []
        time_format_list = []
        time_span = -1

        for match in self.regex.finditer(argument):
            time_value_list.append(float(match.group())) # gets number value

        for entry in self.regex.split(argument):
            if not (entry == "" or entry == None):
                try:
                    float(entry)
                    continue
                except ValueError:
                    time_format_list.append(entry.strip().lower()) # gets h, m, s, etc.

        if (time_format_list == [] or time_value_list == [] 
            or len(time_format_list) != len(time_value_list)):
            raise commands.BadArgument(f"Argument {argument} is not a valid time duration.")

        for i in range(len(time_format_list)):
            if time_span == -1:
                time_span = 0

            time_span += self.to_seconds(time_value_list[i], time_format_list[i])

        if time_span == -1:
            raise commands.BadArgument(f"Argument {argument} is not a valid time duration.")

        return datetime.timedelta(seconds=time_span)

class WizardManager():
    """A class that allows you to make a wizard of sorts, allowing a more intuitive way of getting multiple inputs from a user."""

    def __init__(self, embed_title: str, timeout: float, final_text: str, color = discord.Colour(0x4378fc)):
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

        wizard_embed = discord.Embed(
            title = self.embed_title, 
            colour = self.color
        )
        wizard_embed.set_author(
            name=f"{ctx.bot.user.name}", 
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png', size=128))}"
        )
        wizard_embed.set_footer(text="If you wish to stop this setup at any time, just type in 'exit'.")

        for question in self.questions:
            wizard_embed.description = question[0]

            if not self.ori_mes:
                self.ori_mes = await ctx.reply(embed=wizard_embed)
            else:
                await self.ori_mes.edit(embed=wizard_embed)

            try:
                reply = await ctx.bot.wait_for('message', check=check, timeout=self.timeout)
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
                converted = await discord.utils.maybe_coroutine(question[1], ctx, reply.content)
            except:
                wizard_embed.description = "Invalid input. Exiting..."
                wizard_embed.set_footer(text=discord.Embed.Empty)
                await self.ori_mes.edit(embed=wizard_embed)
                return

            await discord.utils.maybe_coroutine(question[2], ctx, converted)

        wizard_embed.description = self.final_text
        wizard_embed.set_footer(text=discord.Embed.Empty)
        await self.ori_mes.edit(embed=wizard_embed)