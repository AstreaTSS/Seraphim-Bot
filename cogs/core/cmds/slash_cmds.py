import importlib
import random
import typing

import discord
from discord.ext import commands

import common.utils as utils


class SlashCMDS(commands.Cog):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    async def cog_load(self):
        await self.bot.tree.sync()

    @discord.app_commands.command()
    @discord.app_commands.describe(content="The content to reverse.")
    async def reverse(self, inter: discord.Interaction, content: str):
        """Reverses the content given."""
        await inter.response.send_message(f"{content[::-1]}", ephemeral=True)

    @discord.app_commands.command()
    @discord.app_commands.describe(target="The content to kill.")
    async def kill(
        self,
        inter: discord.Interaction,
        *,
        target: str,
    ):
        "Allows you to kill the victim specified using the iconic Minecraft kill command messages."

        if len(target) > 1900:
            raise commands.BadArgument("The target you provided is too large.")

        victim_str = ""

        if not inter.data or not inter.data.get("resolved", None):
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
                discord.utils.escape_markdown(target) if not victim_raw else victim_raw
            )

        victim_str = f"**{victim_str}**"
        author_str = f"**{inter.user.display_name}**"

        kill_msg = random.choice(self.bot.death_messages)
        kill_msg = kill_msg.replace("%1$s", victim_str)
        kill_msg = kill_msg.replace("%2$s", author_str)
        kill_msg = kill_msg.replace("%3$s", "*Seraphim*")
        kill_msg = f"{kill_msg}."

        kill_embed = discord.Embed(colour=discord.Colour.red(), description=kill_msg)
        await inter.response.send_message(embed=kill_embed)


async def setup(bot):
    importlib.reload(utils)
    await bot.add_cog(SlashCMDS(bot))
