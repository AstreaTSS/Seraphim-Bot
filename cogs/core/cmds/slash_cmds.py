import importlib
import random
import typing

import discord
from discord.ext import commands

import common.utils as utils


class SlashCMDS(commands.Cog):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(slash_command=True)
    async def reverse(
        self,
        ctx: commands.Context,
        *,
        content: str = commands.Option(description="The content to reverse."),
    ):
        "Reverses the content given."
        await ctx.reply(content=f"{content[::-1]}", ephemeral=True)

    @commands.command(slash_command=True)
    async def kill(
        self,
        ctx: commands.Context,
        *,
        target: str = commands.Option(description="The content to kill."),
    ):
        "Allows you to kill the victim specified using the iconic Minecraft kill command messages."

        if len(target) > 1900:
            raise commands.BadArgument("The target you provided is too large.")

        victim_str = ""

        if ctx.interaction:
            inter = ctx.interaction

            if not inter.data or not inter.data.get("resolved", False):
                victim_str = discord.utils.escape_markdown(target)
            else:
                victim_raw: typing.Optional[str] = None

                # see if we got any resolved members or users - looks nicer to do
                if (
                    inter.data["resolved"]["members"]
                    and len(inter.data["resolved"]["members"].keys()) == 1
                ):
                    victim_raw = tuple(inter.data["resolved"]["members"].values())[0][
                        "nick"
                    ]  # type: ignore
                if (
                    not victim_raw
                    and inter.data["resolved"]["users"]
                    and len(inter.data["resolved"]["users"].keys()) == 1
                ):
                    victim_raw = tuple(inter.data["resolved"]["users"].values())[0][
                        "username"
                    ]

                victim_str = (
                    discord.utils.escape_markdown(target)
                    if not victim_raw
                    else victim_raw
                )
        else:
            try:
                converter = commands.MemberConverter()
                victim = await converter.convert(ctx, target)
                victim_str = victim.display_name
            except commands.BadArgument:
                victim_str = discord.utils.escape_markdown(target)

        victim_str = f"**{victim_str}**"
        author_str = f"**{ctx.author.display_name}**"

        kill_msg = random.choice(self.bot.death_messages)
        kill_msg = kill_msg.replace("%1$s", victim_str)
        kill_msg = kill_msg.replace("%2$s", author_str)
        kill_msg = kill_msg.replace("%3$s", "*Seraphim*")
        kill_msg = f"{kill_msg}."

        kill_embed = discord.Embed(colour=discord.Colour.red(), description=kill_msg)
        await ctx.reply(embed=kill_embed)


def setup(bot):
    importlib.reload(utils)
    bot.add_cog(SlashCMDS(bot))
