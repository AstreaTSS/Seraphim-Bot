#!/usr/bin/env python3.7
from discord.ext import commands
import discord, time

class NormCMDs(commands.Cog, name="Normal"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Pings the bot. Great way of finding out if the bot’s working correctly."""

        start_time = time.perf_counter()
        ping_discord = round((self.bot.latency * 1000), 2)

        mes = await ctx.send(f"Pong!\n`{ping_discord}` ms from Discord.\nCalculating personal ping...")
        
        end_time = time.perf_counter()
        ping_personal = round(((end_time - start_time) * 1000), 2)
        
        await mes.edit(content=f"Pong!\n`{ping_discord}` ms from Discord.\n`{ping_personal}` ms personally.")
    
    @commands.command()
    async def reverse(self, ctx, *, msg):
        """Reverses the content given."""

        if len(msg) < 1950:
            await ctx.send(f"{ctx.author.mention}: {discord.utils.escape_mentions(msg[::-1])}")
        else:
            await ctx.send(f"{ctx.author.mention}, that message is too long!")

def setup(bot):
    bot.add_cog(NormCMDs(bot))