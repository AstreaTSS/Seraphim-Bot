#!/usr/bin/env python3.7
from discord.ext import commands
from fuzzywuzzy import process, fuzz
import common.utils as utils

import discord, re, collections
import datetime, asyncio

class TimeDurationConverter(commands.Converter):
    # Converts a string to a time duration.

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

class FuzzyMemberConverter(commands.IDConverter):
    """Uses fuzzy matching to match strings to a member.
    Most of this initial code is very similar code to MemberConverter
    Checks for ID then mention, username with discrim, then...
    fuzzy searches via nicks first, then usernames"""

    def get_display_name(self, member):
        """For some reason fuzzywuzzy runs the processor on the query,
        so we use a quick isinstance to make sure everything goes ok
        without losing too much performance as a try error would do."""

        if isinstance(member, discord.Member):
            return member.display_name
        else:
            return member

    def get_name(self, member):
        """Same thing as above, but with a normal name."""
        if isinstance(member, discord.Member):
            return member.name
        else:
            return member
    
    def embed_gen(self, ctx, members):
        members_str = [f"`{m.display_name} ({str(m)})`" for m in members]
        description = collections.deque()
        description.append("Multiple users found. Please choose one of the following, or type cancel.")

        for n in range(len(members_str)):
            description.append(f"{n+1} - {members_str[n]}")

        selection_embed = discord.Embed(
            colour = discord.Colour(0x4378fc), 
            description = "\n".join(description)
        )
        selection_embed.set_author(
            name=f"{ctx.guild.me.name}", 
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='jpg', size=128))}"
        )

        return selection_embed

    async def extract_from_memebers(self, ctx, argument, processor):
        member_list = process.extractBests(argument, ctx.guild.members, processor=processor, scorer=fuzz.token_sort_ratio, score_cutoff=80, limit=5)
        if member_list != []:
            if len(member_list) == 1:
                return member_list[0][0]
            else:
                return await self.selection_handler(ctx, member_list)
        return None

    async def selection_handler(self, ctx, options):
        members = [o[0] for o in options]
        selection_embed = self.embed_gen(ctx, members)
        await ctx.send(embed = selection_embed)
        
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            msg = await ctx.bot.wait_for('message', timeout=15.0, check=check)
        except asyncio.TimeoutError:
            raise commands.BadArgument("No user selected. Canceling command.")

        else:
            if msg.content.lower() == "cancel":
                raise utils.CustomCheckFailure("Canceled command.")
            elif not msg.content.isdigit():
                raise commands.BadArgument("Invalid input. Canceled command.")
            else:
                selection = int(msg.content)
                if selection > len(members):
                    raise commands.BadArgument("Invalid number. Canceled command.")
                else:
                    return members[selection - 1]

    async def convert(self, ctx, argument):
        result = None
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)

        if match != None:
            user_id = int(match.group(1))
            result = ctx.guild.get_member(user_id) or discord.utils.get(ctx.message.mentions, id=user_id)
        elif "#" in argument:
            hash_split = argument.split("#")
            result = discord.utils.get(ctx.guild.members, name=hash_split[0], discriminator=hash_split[1])

        if result == None:
            result = await self.extract_from_memebers(ctx, argument, self.get_display_name)
            if result == None:
                result = await self.extract_from_memebers(ctx, argument, self.get_name)

        if result == None:
            raise commands.BadArgument(f'Member "{argument}" not found.')
        return result