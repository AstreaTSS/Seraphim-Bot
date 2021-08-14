import importlib
import random

import discord
from discord.ext import commands
from discord.types.interactions import ApplicationCommandInteractionData

import common.manage_commands as manage_commands


class SlashCMDS(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.bot.loop.create_task(self.register_cmds())

    def cog_unload(self):
        self.bot.loop.create_task(self.remove_cmds())

    async def register_cmds(self):
        await manage_commands.add_slash_command(
            self.bot.user.id,
            self.bot.http.token,
            None,
            "kill",
            "Allows you to kill the victim specified using the iconic Minecraft kill command messages.",
            [manage_commands.create_option("target", "The target to kill.", 3, True)],
        )

    async def remove_cmds(self):
        await manage_commands.remove_all_commands(self.bot.user.id, self.bot.http.token)

    @commands.Cog.listener()
    async def on_interaction(self, inter: discord.Interaction):
        """An incredibly dirty way of doing slash commands.
        This code is NOT pretty. But it should work.
        """
        if inter.type != discord.InteractionType.application_command:
            return

        data: ApplicationCommandInteractionData = inter.data

        if data["name"] == "kill":
            target = None

            if data.get("resolved"):
                if (
                    data["resolved"].get("members")
                    and len(data["resolved"]["members"].keys()) == 1
                ):
                    target = data["resolved"]["members"][
                        list(data["resolved"]["members"].keys())[0]
                    ]["nick"]
                if (
                    not target
                    and data["resolved"].get("users")
                    and len(data["resolved"]["users"].keys()) == 1
                ):
                    target = data["resolved"]["users"][
                        list(data["resolved"]["users"].keys())[0]
                    ]["username"]

            if not target:
                target = data["options"][0]["value"]

            await self.kill(inter, target)

    async def kill(self, inter: discord.Interaction, target: str):
        if len(target) > 1900:
            await inter.response.send_message(
                content="The target you provided is too long.", ephemeral=True
            )
            return

        victim_str = f"**{target}**"
        author_str = f"**{inter.user.display_name}**" if inter.user else f"**you**"

        kill_msg = random.choice(self.bot.death_messages)

        kill_msg = kill_msg.replace("%1$s", victim_str)
        kill_msg = kill_msg.replace("%2$s", author_str)
        kill_msg = kill_msg.replace("%3$s", "*Seraphim*")
        kill_msg = f"{kill_msg}."

        kill_embed = discord.Embed(colour=discord.Colour.red(), description=kill_msg)

        await inter.response.send_message(embed=kill_embed)


def setup(bot):
    importlib.reload(manage_commands)
    bot.add_cog(SlashCMDS(bot))
