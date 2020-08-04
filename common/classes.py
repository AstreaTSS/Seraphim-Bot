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

class FuzzyConverter(commands.IDConverter):
    """General class for fuzzy matching. Contains functions
    needed to fuzzy convert."""

    def embed_gen(self, ctx, description):
        selection_embed = discord.Embed(
            colour = discord.Colour(0x4378fc), 
            description = "\n".join(description)
        )
        selection_embed.set_author(
            name=f"{ctx.guild.me.name}", 
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='jpg', size=128))}"
        )
        
        return selection_embed

    def norm_embed_gen(self, ctx, list_str):
        description = collections.deque()
        description.append("Multiple entries found. Please choose one of the following, or type cancel.")

        for n in range(len(list_str)):
            description.append(f"{n+1} - `{list_str[n]}`")

        return self.embed_gen(ctx, description)

    def unsure_embed_gen(self, ctx, item):
        description = collections.deque()
        description.append(f"Did you mean `{str(item)}`?.")
        description.append(f"Reply with yes or no.")

        return self.embed_gen(ctx, description)

    async def extract_from_list(self, ctx, argument, list_of_items, processor, scorer, unsure = False):
        fuzzy_list = process.extractBests(argument, list_of_items, processor=processor, scorer=scorer, score_cutoff=80, limit=5)
        if fuzzy_list != []:
            if len(fuzzy_list) == 1:
                if not unsure:
                    return fuzzy_list[0][0] # actual entry itself
                else:
                    if fuzzy_list[0][1] < 95: # entries score
                        await self.unsure_select_handler(ctx, fuzzy_list[0][0])
                    return fuzzy_list[0][0]
            else:
                return await self.selection_handler(ctx, fuzzy_list)
        return None

    async def unsure_select_handler(self, ctx, item):
        selection_embed = self.unsure_embed_gen(ctx, item)
        await ctx.send(embed = selection_embed)

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            msg = await ctx.bot.wait_for('message', timeout=15.0, check=check)
        except asyncio.TimeoutError:
            raise commands.BadArgument("No option selected. Canceling command.")

        else:
            lowered = msg.content.lower()

            # yes, this snippet is copied from the source of d.py, but it's slightly edited so...
            if lowered in ('yes', 'y', 'true', 't', '1'):
                return
            elif lowered in ('no', 'n', 'false', 'f', '0'):
                raise utils.CustomCheckFailure("Couldn't verify the entry. Canceled command.")
            else:
                raise commands.BadArgument("Invalid input. Canceled command.")

    async def selection_handler(self, ctx, options):
        entries = [o[0] for o in options]
        selection_embed = self.norm_embed_gen(ctx, entries)
        await ctx.send(embed = selection_embed)
        
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            msg = await ctx.bot.wait_for('message', timeout=15.0, check=check)
        except asyncio.TimeoutError:
            raise commands.BadArgument("No entry selected. Canceling command.")

        else:
            if msg.content.lower() == "cancel":
                raise utils.CustomCheckFailure("Canceled command.")
            elif not msg.content.isdigit():
                raise commands.BadArgument("Invalid input. Canceled command.")
            else:
                selection = int(msg.content)
                if selection > len(entries):
                    raise commands.BadArgument("Invalid number. Canceled command.")
                else:
                    return entries[selection - 1]

class FuzzyMemberConverter(FuzzyConverter):
    """Uses fuzzy matching to match strings to a member.
    Most of this initial code is very similar code to MemberConverter
    Checks for ID then mention, username with discrim, then...
    fuzzy searches via nicks first, then usernames"""

    def norm_embed_gen(self, ctx, entries):
        list_str = [f"`{m.display_name} ({str(m)})`" for m in entries]

        description = collections.deque()
        description.append("Multiple entries found. Please choose one of the following, or type cancel.")

        for n in range(len(list_str)):
            description.append(f"{n+1} - {list_str[n]}")

        return self.embed_gen(ctx, description)

    def get_display_name(self, member):
        """For some reason fuzzywuzzy runs the processor on the query,
        so we use a quick isinstance to make sure everything goes ok
        without losing too much performance as a try error would do."""

        if isinstance(member, discord.Member):
            return member.display_name.lower()
        else:
            return member

    def get_name(self, member):
        """Same thing as above, but with a normal name."""
        if isinstance(member, discord.Member):
            return member.name.lower()
        else:
            return member

    async def multi_extract(self, ctx, argument, list_of_items, processors, scorers):
        combined_list = []

        for scorer in scorers:
            for processor in processors:
                fuzzy_list = process.extractBests(argument, list_of_items, processor=processor, scorer=scorer, score_cutoff=80, limit=5)
                if fuzzy_list != []:
                    new_members = [e for e in fuzzy_list if not e[0] in combined_list]
                    combined_list.extend(new_members)

                    if len(combined_list) > 3:
                        return await self.selection_handler(ctx, combined_list)

        if combined_list != []:
            if len(combined_list) == 1:
                return combined_list[0][0]
            else:
                return await self.selection_handler(ctx, combined_list)
        else:
            return None

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
            result = await self.multi_extract(ctx, argument, ctx.guild.members, [self.get_display_name, self.get_name], [fuzz.token_set_ratio, fuzz.token_set_ratio])

        if result == None:
            raise commands.BadArgument(f'Member "{argument}" not found.')
        return result

class FuzzyRoleConverter(FuzzyConverter):
    """Uses fuzzy matching to match strings to a role.
    ID, mention, then name. Since getting the wrong role can be dangerous, we take
    some extra steps just in case."""

    def get_name(self, role):
        if isinstance(role, discord.Role):
            return role.name.lower()
        else:
            return role

    async def convert(self, ctx, argument):
        result = None
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)

        if match != None:
            role_id = int(match.group(1))
            result = ctx.guild.get_role(role_id)

        if result == None:
            result = await self.extract_from_list(ctx, argument, ctx.guild.roles, self.get_name, fuzz.ratio, unsure=True)
        
        if result == None:
            raise commands.BadArgument(f'Role "{argument}" not found.')
        return result
