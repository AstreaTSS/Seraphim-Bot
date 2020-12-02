#!/usr/bin/env python3.7
from discord.ext import commands
import discord, re, datetime, asyncio

class SnipedMessage():
    """A special class for sniped messages, using slots to keep the memory usage to a minimum."""
    __slots__ = ("embed", "time_modified")

    def __init__(self, embed: discord.Embed):
        self.embed = embed
        self.time_modified = datetime.datetime.utcnow()

class SetAsyncQueue(asyncio.Queue):
    """A special type of async queue that uses a set instead of a queue.
    Useful when we don't want duplicates."""
    def _init(self, maxsize):
        self._queue = set()
    def _get(self):
        return self._queue.pop()
    def _put(self, item):
        self._queue.add(item)

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