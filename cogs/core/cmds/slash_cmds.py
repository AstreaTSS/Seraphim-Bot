import importlib
import random

import discord
from discord.ext import commands
from discord.types.interactions import ApplicationCommandInteractionData

import common.manage_commands as manage_commands


class SlashCMDS(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(hidden=True)
    async def register_slash_cmds(self, ctx):
        await manage_commands.add_slash_command(
            self.bot.user.id,
            self.bot.http.token,
            None,
            "kill",
            "Allows you to kill the victim specified using the iconic Minecraft kill command messages.",
            [manage_commands.create_option("target", "The target to kill.", 3, True)],
        )

        await ctx.reply("Done!")

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
                # happens if the content has stuff like user/role/channel data from a mention
                if (
                    data["resolved"].get("members")
                    and len(data["resolved"]["members"].keys()) == 1
                ):
                    # if there are resolved member objects and there are only one of them
                    # i'd rather not deal with making the kill cmd deal with 2+ targets
                    target = data["resolved"]["members"][
                        list(data["resolved"]["members"].keys())[0]
                    ]["nick"]
                    # the above is more confusing than it should be
                    # basically, it gets the first (and only) member from the resolved members
                    # (to do so, we have to get a list of every key in the members thing since
                    # discord doesn't provide the data in a list, and then get the only key in there
                    # and then get the members nickname, if it has any)
                if (
                    not target
                    and data["resolved"].get("users")
                    and len(data["resolved"]["users"].keys()) == 1
                ):
                    # same as member check, but for users, and we see if we already got a member first
                    target = data["resolved"]["users"][
                        list(data["resolved"]["users"].keys())[0]
                    ]["username"]

            if not target:
                target = data["options"][0][
                    "value"
                ]  # just the stuff in the target value

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
