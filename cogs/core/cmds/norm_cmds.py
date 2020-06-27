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

    @commands.command()
    async def about(self, ctx):
        """Gives information about the bot."""

        msg_list = []

        msg_list.append("Hi! I'm Seraphim, Sonic49's personal bot!")
        msg_list.append("I was created initially as a starboard bot as other starboard bots had poor uptime, " +
        "but I've since been expanded to other functions, too.")
        msg_list.append("I tend to have features that are either done poorly by other bots, or features of bots " +
        "that tend to be offline/unresponsive for a decent amount of time.")
        msg_list.append("You cannot invite me to your server. Usually, Sonic49 invites me to one of his servers on his own, " +
        "but you might be able to convince him, although unlikely, to invite me to your server.") 

        about_embed = discord.Embed(
            title = "About me, Seraphim", 
            colour = discord.Colour(0x4378fc), 
            description = "\n\n".join(msg_list)
        )
        about_embed.set_author(
            name=f"{self.bot.user.name}", 
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format='jpg', size=128))}"
        )

        source_list = []
        source_list.append("My source code is [here!](https://github.com/Sonic4999/Seraphim-Bot)")
        source_list.append("This code might not be the best code out there, but you may have some use for it.")

        about_embed.add_field(
            name = "Source Code",
            value = "\n".join(source_list),
            inline = False
        )

        await ctx.send(embed=about_embed)

def setup(bot):
    bot.add_cog(NormCMDs(bot))