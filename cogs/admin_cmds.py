#!/usr/bin/env python3.7
from discord.ext import commands
import discord

import cogs.star_universals as star_univ
import cogs.star_mes_handler as star_mes

async def proper_permissions(ctx):
    permissions = ctx.author.guild_permissions
    return (permissions.administrator or permissions.manage_messages)

class AdminCMDS(commands.Cog):
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
    @commands.check(proper_permissions)
    async def force(self, ctx, mes_id):
        if not mes_id.isdigit():
            await ctx.send("Not a valid channel id!")
            return

        try:
            mes = await ctx.channel.fetch_message(int(mes_id))
        except discord.NotFound:
            await ctx.send("Message not found! Is this a valid message ID and are you running this command in the same channel as the message?")
            return

        starboard_entry = star_univ.get_star_entry(self.bot, mes.id)
        if starboard_entry == []:
            self.bot.starboard[mes.id] = {
                "ori_chan_id": mes.channel.id,
                "star_var_id": None,
                "author_id": mes.author.id,
                "ori_reactors": "",
                "var_reactors": "",
                "guild_id": mes.guild.id,
                "forced": True,

                "ori_mes_id_bac": mes.id,
                "passed_star_limit": False
            }
            starboard_entry = self.bot.starboard[mes.id]
        elif starboard_entry["star_var_id"] == None:
            starboard_entry["forced"] == True
        else:
            await ctx.send("This message is already on the starboard!")
            return
        
        unique_stars = star_univ.get_num_stars(starboard_entry)
        await star_mes.star_mes(self.bot, mes, unique_stars, forced=True)

def setup(bot):
    bot.add_cog(AdminCMDS(bot))