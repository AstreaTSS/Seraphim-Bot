#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib, collections
import datetime, random

import common.fuzzys as fuzzys
import common.star_utils as star_utils
import common.utils as utils
import common.star_mes_handler as star_mes
import common.star_classes as star_classes
import common.groups as groups

class StarCMDs(commands.Cog, name = "Starboard"):
    """Commands for the starboard. See the settings command to set up the starboard."""

    def __init__(self, bot):
        self.bot = bot

    def get_star_rankings(self, ctx):
        user_star_dict = collections.Counter()
        guild_entries = self.bot.starboard.get_list(lambda e: e.guild_id == ctx.guild.id)

        if guild_entries != []:
            for entry in guild_entries:
                if entry.author_id in user_star_dict.keys():
                    user_star_dict[entry.author_id] += len(entry.get_reactors())
                else:
                    user_star_dict[entry.author_id] = len(entry.get_reactors())

            return user_star_dict.most_common(None)
        else:
            return None

    def get_user_placing(self, user_star_list, author_id):
        author_entry = discord.utils.find(lambda e: e[0] == author_id, user_star_list)
        if author_entry != None:
            author_index = user_star_list.index(author_entry)
            return f"position: #{author_index + 1} with {author_entry[1]} ⭐"
        else:
            return "position: N/A - no stars found!"
    
    async def cog_check(self, ctx):
        return self.bot.config[ctx.guild.id]["star_toggle"]

    @groups.group(invoke_without_command=True, aliases = ["starboard", "star"], ignore_extra=False)
    async def sb(self, ctx):
        """Base command for running starboard commands. Use the help command for this to get more info."""
        await ctx.send_help(ctx.command)

    @sb.command(aliases = ["msg_top"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def msgtop(self, ctx):
        """Allows you to view the top 10 starred messages on a server. Cooldown of once every 5 seconds per user."""

        guild_entries = self.bot.starboard.get_list(lambda e: e.guild_id == ctx.guild.id)
        if guild_entries != []:
            top_embed = discord.Embed(title=f"Top starred messages in {ctx.guild.name}", colour=discord.Colour(0xcfca76), timestamp=datetime.datetime.utcnow())
            top_embed.set_author(name=f"{self.bot.user.name}", icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png', size=128))}")
            top_embed.set_footer(text="As of")

            guild_entries.sort(reverse=True, key=lambda e: len(e.get_reactors()))

            for i in range(len(guild_entries)):
                if i > 9:
                    break

                entry = guild_entries[i]
                starboard_id = entry.starboard_id

                url = f"https://discordapp.com/channels/{ctx.guild.id}/{starboard_id}/{entry.star_var_id}"
                num_stars = len(entry.get_reactors())
                member = await utils.user_from_id(self.bot, ctx.guild, entry.author_id)
                author_str = f"{member.display_name} ({str(member)})" if member != None else f"User ID: {entry.author_id}"

                top_embed.add_field(name=f"#{i+1}: {num_stars} ⭐ from {author_str}", value=f"[Message]({url})\n", inline=False)

            await ctx.send(embed=top_embed)
        else:
            raise utils.CustomCheckFailure("There are no starboard entries for this server!")

    @sb.command(name = "top", aliases = ["leaderboard", "lb"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def top(self, ctx):
        """Allows you to view the top 10 people with the most stars on a server. Cooldown of once every 5 seconds per user."""

        user_star_list = self.get_star_rankings(ctx)

        if user_star_list != None:
            top_embed = discord.Embed(title=f"Star Leaderboard for {ctx.guild.name}", colour=discord.Colour(0xcfca76), timestamp=datetime.datetime.utcnow())
            top_embed.set_author(name=f"{self.bot.user.name}", icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png', size=128))}")

            for i in range(len(user_star_list)):
                if i > 9:
                    break
                entry = user_star_list[i]

                member = await utils.user_from_id(self.bot, ctx.guild, entry[0])
                num_stars = entry[1]
                author_str = f"{member.display_name} ({str(member)})" if member != None else f"User ID: {entry[0]}"

                top_embed.add_field(name=f"#{i+1}: {author_str}", value=f"{num_stars} ⭐\n", inline=False)

            top_embed.set_footer(text=f"Your {self.get_user_placing(user_star_list, ctx.author.id)}")
            await ctx.send(embed=top_embed)
        else:
            raise utils.CustomCheckFailure("There are no starboard entries for this server!")

    @sb.command(aliases = ["position", "place", "placing"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def pos(self, ctx, *, user = None):
        """Allows you to get either your or whoever you mentioned’s position in the star leaderboard (like the top command, but only for one person).
        The user can be mentioned, searched up by ID, or you can say their name and the bot will attempt to search for that person."""

        if user != None:
            member = await fuzzys.FuzzyMemberConverter().convert(ctx, user)
        else:
            member = ctx.author

        user_star_list = self.get_star_rankings(ctx)

        if user_star_list != None:
            if user != None:
                placing = f"{member.display_name}'s {self.get_user_placing(user_star_list, member.id)}"
            else:
                placing = f"Your {self.get_user_placing(user_star_list, member.id)}"

            place_embed = discord.Embed(colour=discord.Colour(0xcfca76), description=placing, timestamp=datetime.datetime.utcnow())
            place_embed.set_author(name=f"{self.bot.user.name}", icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png',size=128))}")
            place_embed.set_footer(text="Sent")

            await ctx.send(embed=place_embed)
        else:
            raise utils.CustomCheckFailure("There are no starboard entries for this server!")

    @sb.command()
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def random(self, ctx):
        """Gets a random starboard entry from the server it's being run in.
        May not work 100% of the time, but it should be reliable enough."""

        valid_entries = self.bot.starboard.get_list(lambda e: e.guild_id == ctx.guild.id and e.star_var_id != None)

        if valid_entries:
            random_entry = random.choice(valid_entries)
            starboard_id = random_entry.starboard_id

            starboard_chan = ctx.guild.get_channel(starboard_id)
            if starboard_chan == None:
                raise utils.CustomCheckFailure("I couldn't find the starboard channel for the entry I picked.")

            try:
                star_mes = await starboard_chan.fetch_message(random_entry.star_var_id)
            except discord.HTTPException:
                ori_url = f"https://discordapp.com/channels/{ctx.guild.id}/{random_entry.ori_chan_id}/{random_entry.ori_mes_id}"
                await ctx.send("I picked an entry, but I couldn't get the starboard message.\n" +
                f"This might be the message I was trying to get: {ori_url}")
                return

            star_content = star_mes.content
            star_embed = star_mes.embeds[0]

            star_embed.add_field(name="Starboard Variant", value=f"[Jump]({star_mes.jump_url})", inline=True)

            await ctx.send(star_content, embed=star_embed)
        else:
            await ctx.send("There are no starboard entries for me to pick!")

    @sb.command()
    @commands.check(utils.proper_permissions)
    async def force(self, ctx, msg: discord.Message):
        """Forces a message onto the starboard, regardless of how many stars it has.
        The message either needs to be a message ID of a message in the channel the command is being run in,
        a {channel id}-{message id} format, or the message link itself.
        This message cannot be taken off the starboard unless it is deleted from it manually.
        You must have Manage Server permissions or higher to run this command."""
        
        if not self.bot.config[ctx.guild.id]["star_toggle"]:
            raise utils.CustomCheckFailure("Starboard is not turned on for this server!")

        starboard_entry = self.bot.starboard.get(msg.id)
        if not starboard_entry:
            author_id = star_utils.get_author_id(msg, self.bot)
            starboard_entry = star_classes.StarboardEntry.new_entry(msg, author_id, None, forced=True)
            self.bot.starboard.add(starboard_entry)

            await star_utils.sync_prev_reactors(self.bot, msg, author_id, starboard_entry,
                star_classes.ReactorType.ORI_REACTORS, remove=False)
        
        if starboard_entry.star_var_id == None:
            starboard_entry.forced == True
        else:
            raise commands.BadArgument("This message is already on the starboard!")
        
        self.bot.star_queue.put([msg.channel.id, msg.id, msg.guild.id])
        await ctx.send("Done! Please wait a couple of seconds for the message to appear.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def debug_star_mes(self, ctx, msg: discord.Message):
        send_embed = await star_mes.star_generate(self.bot, msg)
        await ctx.send(embed=send_embed)

def setup(bot):
    importlib.reload(star_utils)
    importlib.reload(star_mes)
    importlib.reload(utils)
    importlib.reload(fuzzys)
    importlib.reload(groups)
    
    bot.add_cog(StarCMDs(bot))