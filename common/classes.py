#!/usr/bin/env python3.7
from discord.ext import commands
import common.utils as utils

import discord, re, datetime

class SnipedMessage():
    """A special class for sniped messages, using slots to keep the memory usage to a minimum."""
    __slots__ = ("author_name", "author_url", "content", "created_at", "time_modified")

    def __init__(self, message: discord.Message, now: datetime.datetime):
        self.author_name = f"{message.author.display_name} ({str(message.author)})"
        self.author_url = str(message.author.avatar_url_as(format=None,static_format='png', size=128))
        self.content = utils.get_content(message)
        self.created_at = message.created_at
        self.time_modified = now

    def __repr__(self):
        return f"<SnipedMessage author_name={self.author_name} author_url={self.author_url} created_at={self.created_at} time_modified={self.time_modified}>"

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