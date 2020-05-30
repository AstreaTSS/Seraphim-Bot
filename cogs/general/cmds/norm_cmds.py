#!/usr/bin/env python3.7
from discord.ext import commands
import discord, datetime

class NormCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):

        help_embed = discord.Embed(
            title = "To see the list of commands and how to use them, please use the below link:", 
            colour = discord.Colour(0x4378fc), 
            description = "https://tinyurl.com/SonicsStarboardHelp"
        )
        help_embed.set_author(
            name=f"{self.bot.user.name}", 
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format='jpg', size=128))}"
        )

        await ctx.send(embed=help_embed)

    @commands.command()
    async def ping(self, ctx):
        current_time = datetime.datetime.utcnow().timestamp()
        mes_time = ctx.message.created_at.timestamp()

        ping_discord = round((self.bot.latency * 1000), 2)
        ping_personal = round((current_time - mes_time) * 1000, 2)

        await ctx.send(f"Pong!\n`{ping_discord}` ms from discord.\n`{ping_personal}` ms personally (not accurate)")
    
    @commands.command()
    async def reverse(self, ctx, *, msg):
        if len(msg) < 1950:
            await ctx.send(f"{ctx.author.mention}: {discord.utils.escape_mentions(msg[::-1])}")
        else:
            await ctx.send(f"{ctx.author.mention}, that message is too long!")

def setup(bot):
    bot.add_cog(NormCMDs(bot))