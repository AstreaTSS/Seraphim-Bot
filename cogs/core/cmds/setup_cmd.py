#!/usr/bin/env python3.7
from discord import embeds
from discord.ext import commands
import discord, asyncio

import common.utils as utils
import common.groups as groups

class SetupCMD(commands.Cog, name="Setup"):
    def __init__(self, bot):
        self.bot = bot

    @groups.group()
    @commands.check(utils.proper_permissions)
    async def setup(self, ctx):
        """The base command for using the setup commands. See the help for the subcommands for more info.
        Only people with Manage Server permissions or higher can use these commands.
        This command is in beta. It may be unstable."""
        
        if ctx.invoked_subcommand == None:
            await ctx.send_help(ctx.command)

    @setup.command(aliases=["sb"])
    @commands.check(utils.proper_permissions)
    async def starboard(self, ctx: commands.Context):
        """Allows you to set up the starboard for Seraphim in an easy-to-understand way.
        Only people with Manage Server permissions or higher can use these commands.
        This command is in beta. It may be unstable."""

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        body_str = "".join((
            "Starboard, the reason why this bot exists in the first place. If you're setting this up, ",
            "I assume you know what it is.\n\n",
            "First off: what channel do you want the starboard in? This must be a channel the bot can ",
            "see, send and delete message, and react in. It also must already exist. You can mention it, ",
            "say the channel name exactly as is, or put the ID of it."
        ))

        setup_embed = discord.Embed(
            title = "Starboard Setup", 
            colour = discord.Colour(0x4378fc), 
            description = body_str
        )
        setup_embed.set_author(
            name=f"{self.bot.user.name}", 
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png', size=128))}"
        )
        setup_embed.set_footer(text="If you wish to stop this setup at any time, just type in 'exit'.")

        ori_mes = await ctx.reply(embed=setup_embed)

        try:
            reply = await self.bot.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            setup_embed.description = "Failed to reply. Exiting..."
            setup_embed.set_footer(text=discord.Embed.Empty)
            await ori_mes.edit(embed=setup_embed)
            return
        else:
            if reply.content.lower() == "exit":
                setup_embed.description = "Exiting..."
                setup_embed.set_footer(text=discord.Embed.Empty)
                await ori_mes.edit(embed=setup_embed)
                return

        try:
            star_chan = commands.TextChannelConverter().convert(ctx, reply)
        except commands.BadArgument:
            setup_embed.description = "Invalid input. Exiting..."
            setup_embed.set_footer(text=discord.Embed.Empty)
            await ori_mes.edit(embed=setup_embed)
            return

        ctx.bot.config[ctx.guild.id]["starboard_id"] = star_chan.id

        body_str = "".join((
            "Well that's done with. Now for a more tricky question: what do you want the star limit to be?\n",
            "The star limit is how many stars a message needs to be on the starboard. Sometimes, this is called ",
            "the 'required' amount, as it's the amount required to be on the starboard. Either or. Just type a number."
        ))

        setup_embed.description = body_str
        await ori_mes.edit(embed=setup_embed)

        try:
            reply = await self.bot.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            setup_embed.description = "Failed to reply. Exiting..."
            setup_embed.set_footer(text=discord.Embed.Empty)
            await ori_mes.edit(embed=setup_embed)
            return
        else:
            if reply.content.lower() == "exit":
                setup_embed.description = "Exiting..."
                setup_embed.set_footer(text=discord.Embed.Empty)
                await ori_mes.edit(embed=setup_embed)
                return

        try:
            limit = int(reply)
        except TypeError:
            setup_embed.description = "Invalid input. Exiting..."
            setup_embed.set_footer(text=discord.Embed.Empty)
            await ori_mes.edit(embed=setup_embed)
            return

        ctx.bot.config[ctx.guild.id]["star_limit"] = limit

        body_str = "Final question: do you want to enable the starboard? A simple 'yes' or 'no' will do."

        setup_embed.description = body_str
        await ori_mes.edit(embed=setup_embed)

        try:
            reply = await self.bot.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            setup_embed.description = "Failed to reply. Exiting..."
            setup_embed.set_footer(text=discord.Embed.Empty)
            await ori_mes.edit(embed=setup_embed)
            return
        else:
            if reply.content.lower() == "exit":
                setup_embed.description = "Exiting..."
                setup_embed.set_footer(text=discord.Embed.Empty)
                await ori_mes.edit(embed=setup_embed)
                return

        lowered = reply.content.lower()

        if lowered in ('yes', 'y', 'true', 't', '1'):
            ctx.bot.config[ctx.guild.id]["star_toggle"] = True
        elif lowered in ('no', 'n', 'false', 'f', '0'):
            pass
        else:
            setup_embed.description = "Invalid input. Exiting..."
            setup_embed.set_footer(text=discord.Embed.Empty)
            await ori_mes.edit(embed=setup_embed)
            return

        body_str = "".join((
            "The setup is done. If you wish to view more options for the starboard, I suggest ",
            f"looking at `{ctx.prefix}settings starboard` command."
        ))

        setup_embed.description = body_str
        await ori_mes.edit(embed=setup_embed)

def setup(bot):
    bot.add_cog(SetupCMD(bot))