#!/usr/bin/env python3.7
from discord.ext import commands
import discord

import star_utils.star_universals as star_univ
import star_utils.universals as univ
import star_utils.star_mes_handler as star_mes

class AdminCMDS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return univ.proper_permissions(ctx)

    @commands.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        self.bot.star_config[ctx.guild.id]["starboard_id"] = channel.id
        await ctx.send(f"Set channel to {channel.mention}!")

    @commands.command()
    async def limit(self, ctx, limit):
        if limit.isdigit():
            self.bot.star_config[ctx.guild.id]["star_limit"] = int(limit)
            await ctx.send(f"Set limit to {limit}!")
        else:
            await ctx.send("That doesn't seem like a valid number to me...")

    @commands.command()
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
        await star_mes.send(self.bot, mes, unique_stars, forced=True)

def setup(bot):
    bot.add_cog(AdminCMDS(bot))