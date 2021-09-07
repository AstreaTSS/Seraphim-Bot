#!/usr/bin/env python3.8
import collections
import importlib
import random
import time
import typing

import discord
from discord.ext import commands

import common.utils as utils


class NormCMDs(commands.Cog, name="Normal"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Pings the bot. Great way of finding out if the bot’s working correctly, but otherwise has no real use."""

        start_time = time.perf_counter()
        ping_discord = round((self.bot.latency * 1000), 2)

        mes = await ctx.reply(
            f"Pong!\n`{ping_discord}` ms from Discord.\nCalculating personal ping..."
        )

        end_time = time.perf_counter()
        ping_personal = round(((end_time - start_time) * 1000), 2)

        await mes.edit(
            content=f"Pong!\n`{ping_discord}` ms from Discord.\n`{ping_personal}` ms personally."
        )

    @commands.command()
    async def reverse(self, ctx, *, content):
        """Reverses the content given. Only will ping what you can ping."""

        if len(content) < 1975:
            allowed_mentions = utils.deny_mentions(ctx.author)
            await ctx.reply(
                f"{ctx.author.mention}: {content[::-1]}",
                allowed_mentions=allowed_mentions,
            )
        else:
            await ctx.reply(f"{ctx.author.mention}, that message is too long!")

    @commands.command()
    async def kill(
        self, ctx: commands.Context, target: typing.Union[discord.Member, str]
    ):
        "Allows you to kill the victim specified using the iconic Minecraft kill command messages."
        if len(str(target)) > 1900:
            await ctx.send(content="The content you provided is too long.")
            return

        if isinstance(target, discord.Member):
            victim_str = f"**{target.display_name}**"
        else:
            victim_str = f"**{discord.utils.escape_markdown(target)}**"

        author_str = f"**{ctx.author.display_name}**"
        kill_msg = random.choice(self.bot.death_messages)

        kill_msg = kill_msg.replace("%1$s", victim_str)
        kill_msg = kill_msg.replace("%2$s", author_str)
        kill_msg = kill_msg.replace("%3$s", "*Seraphim*")
        kill_msg = f"{kill_msg}."

        kill_embed = discord.Embed(colour=discord.Colour.red(), description=kill_msg)

        await ctx.send(embeds=[kill_embed])

    @commands.command()
    async def support(self, ctx):
        """Gives an invite link to the support server."""
        await ctx.reply("Support server:\nhttps://discord.gg/NSdetwGjpK")

    @commands.command(aliases=["documentation", "doc", "docs"])
    async def wiki(self, ctx):
        """Gives a link for Seraphim's wiki."""
        await ctx.reply("Seraphim's wiki:\nhttps://astrea.gitbook.io/seraphim/")

    @commands.command()
    async def invite(self, ctx):
        """Gives an invite link to invite the bot."""
        await ctx.reply(
            "Invite:\nhttps://discord.com/api/oauth2/authorize?client_id=700857077672706120&permissions=8&scope=bot%20applications.commands"
        )

    @commands.command()
    async def about(self, ctx):
        """Gives information about the bot."""

        msg_list = (
            collections.deque()
        )  # is this pointless? yeah, mostly (there's a slight performance boost), but why not

        msg_list.append("Hi! I'm Seraphim, Astrea's personal bot!")
        msg_list.append(
            "I was created initially as a starboard bot as other starboard bots had poor uptime, "
            + "but I've since been expanded to other functions, too."
        )
        msg_list.append(
            "I tend to have features that are either done poorly by other bots, or features of bots "
            + "that tend to be offline/unresponsive for a decent amount of time."
        )
        msg_list.append(
            "If you want to invite me, you're in luck. The link is: https://discord.com/api/oauth2/authorize?client_id=700857077672706120&permissions=8&scope=bot%20applications.commands"
        )
        msg_list.append(
            "If you need support for me, maybe take a look at the support server here:\nhttps://discord.gg/NSdetwGjpK"
        )

        about_embed = discord.Embed(
            title="About",
            colour=discord.Colour(0x4378FC),
            description="\n\n".join(msg_list),
        )
        about_embed.set_author(
            name=f"{self.bot.user.name}",
            icon_url=utils.get_icon_url(ctx.guild.me.display_avatar),
        )

        source_list = collections.deque()
        source_list.append(
            "My source code is [here!](https://github.com/Astrea49/Seraphim-Bot)"
        )
        source_list.append(
            "This code might not be the best code out there, but you may have some use for it."
        )

        about_embed.add_field(
            name="Source Code", value="\n".join(source_list), inline=False
        )

        await ctx.reply(embed=about_embed)

    @commands.group(invoke_without_command=True, aliases=["prefix"], ignore_extra=False)
    async def prefixes(self, ctx):
        """A way of getting all of the prefixes for this server. You can also add and remove prefixes via this command."""
        prefixes = [f"{p}" for p in self.bot.config.getattr(ctx.guild.id, "prefixes")]
        await ctx.reply(
            f"My prefixes for this server are: `{', '.join(prefixes)}`, but you can also mention me."
        )

    @prefixes.command(ignore_extra=False)
    @utils.proper_permissions()
    async def add(self, ctx, prefix):
        """Addes the prefix to the bot for the server this command is used in, allowing it to be used for commands of the bot.
        If it's more than one word or has a space at the end, surround the prefix with quotes so it doesn't get lost."""

        prefixes = self.bot.config.getattr(ctx.guild.id, "prefixes")

        if len(prefixes) >= 10:
            raise utils.CustomCheckFailure(
                "You have too many prefixes! You can only have up to 10 prefixes."
            )

        if prefix not in prefixes:
            prefixes.append(prefix)
            self.bot.config.setattr(ctx.guild.id, prefixes=prefixes)
            await ctx.reply(f"Added `{prefix}`!")
        else:
            raise commands.BadArgument("The server already has this prefix!")

    @prefixes.command(ignore_extra=False, aliases=["delete"])
    @utils.proper_permissions()
    async def remove(self, ctx, prefix):
        """Deletes a prefix from the bot from the server this command is used in. The prefix must have existed in the first place.
        If it's more than one word or has a space at the end, surround the prefix with quotes so it doesn't get lost."""

        try:
            prefixes = self.bot.config.getattr(ctx.guild.id, "prefixes")
            prefixes.remove(prefix)
            self.bot.config.setattr(ctx.guild.id, prefixes=prefixes)
            await ctx.reply(f"Removed `{prefix}`!")
        except ValueError:
            raise commands.BadArgument(
                "The server doesn't have that prefix, so I can't delete it!"
            )


def setup(bot):
    importlib.reload(utils)
    bot.add_cog(NormCMDs(bot))
