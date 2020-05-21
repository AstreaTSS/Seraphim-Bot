#!/usr/bin/env python3.7
from discord.ext import commands
import discord, datetime

async def proper_permissions(ctx):
    permissions = ctx.author.guild_permissions
    return (permissions.administrator or permissions.manage_messages)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(proper_permissions)
    async def channel(self, ctx, channel: discord.TextChannel):
        self.bot.star_config[ctx.guild.id]["starboard_id"] = channel.id
        await ctx.send(f"Set channel to {channel.mention}!")

    @commands.command()
    @commands.check(proper_permissions)
    async def limit(self, ctx, limit):
        if limit.isdigit():
            self.bot.star_config[ctx.guild.id]["star_limit"] = int(limit)
            await ctx.send(f"Set limit to {limit}!")
        else:
            await ctx.send("That doesn't seem like a valid number to me...")

    @commands.group()
    @commands.check(proper_permissions)
    async def blacklist(self, ctx):
        if ctx.invoked_subcommand == None:
            list_cmd = self.bot.get_command("blacklist list")
            await ctx.invoke(list_cmd)

    @blacklist.command(name = "list")
    async def _list(self, ctx):
        channel_id_list = [int(c) for c in self.bot.star_config[ctx.guild.id]["blacklist"].split(",") if c != ""]
        if channel_id_list != []:
            channel_mentions = []

            for channel_id in channel_id_list:
                channel = await self.bot.fetch_channel(channel_id)
                channel_mentions.append(channel.mention)

            await ctx.send(f"Blacklisted channels: {', '.join(channel_mentions)}")
        else:
            await ctx.send("There's no blacklisted channels for this guild!")

    @blacklist.command()
    async def add(self, ctx, channel: discord.TextChannel):
        channel_id_list = [int(c) for c in self.bot.star_config[ctx.guild.id]["blacklist"].split(",") if c != ""]

        if not channel.id in channel_id_list:
            channel_id_list.append(channel.id)
            self.bot.star_config[ctx.guild.id]["blacklist"] = ",".join([str(c) for c in channel_id_list])
            await ctx.send(f"Addded {channel.mention} to the blacklist!")
        else:
            await ctx.send("That channel's already in the blacklist!")

    @blacklist.command()
    async def remove(self, ctx, channel: discord.TextChannel):
        channel_id_list = [int(c) for c in self.bot.star_config[ctx.guild.id]["blacklist"].split(",") if c != ""]

        if channel.id in channel_id_list:
            channel_id_list.remove(channel.id)
            self.bot.star_config[ctx.guild.id]["blacklist"] = ",".join([str(c) for c in channel_id_list])
            await ctx.send(f"Removed {channel.mention} from the blacklist!")
        else:
            await ctx.send("That channel's not in the blacklist!")

    @commands.command()
    async def help(self, ctx):
        await ctx.send("There are a couple of commands:\n\n`s!channel <channel mention>` - sets the starboard channel.\n" +
        "`s!limit <limit - positive number>` - sets the minimum number of stars needed to appear on the starboard.\n" +
        "`s!blacklist <optional: list, add, remove>` - allows for control over the blacklist that prevents " +
        "messages from being starred in that channel. With no arguments or with `list`, the bot will just report " +
        "the blacklisted channels. `add` and `remove` *require a channel mention* and allows you to add or remove " +
        "a channel from the blacklist.\n\n"
        "`s!ping` - gets the ping of the bot. Not really something you need to use unless you're the bot maker.\n" +
        "`s!help` - displays this message.")

    @commands.command()
    async def ping(self, ctx):
        current_time = datetime.datetime.utcnow().timestamp()
        mes_time = ctx.message.created_at.timestamp()

        ping_discord = round((self.bot.latency * 1000), 2)
        ping_personal = round((current_time - mes_time) * 1000, 2)

        await ctx.send(f"Pong!\n`{ping_discord}` ms from discord.\n`{ping_personal}` ms personally (not accurate)")

def setup(bot):
    bot.add_cog(Commands(bot))