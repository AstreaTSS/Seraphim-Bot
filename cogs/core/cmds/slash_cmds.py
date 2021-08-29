import importlib
import random

import discord
import dislash
from discord.ext import commands

import common.utils as utils


class SlashCMDS(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @dislash.slash_command(
        description="Reverses the content given.",
        options=[
            dislash.Option(
                "content", "The content to reverse.", dislash.OptionType.STRING, True
            )
        ],
    )
    async def reverse(self, inter: dislash.SlashInteraction, content: str):
        await inter.reply(content=f"{content[::-1]}", ephemeral=True)

    @dislash.slash_command(
        description="Allows you to kill the victim specified using the iconic Minecraft kill command messages.",
        options=[
            dislash.Option(
                "target", "The content to kill.", dislash.OptionType.STRING, True
            )
        ],
    )
    async def kill(self, inter: dislash.SlashInteraction, target: str):
        if len(target) > 1900:
            raise dislash.BadArgument("The target you provided is too large.")

        victim_str = ""

        # see if we got any resolved members or users - looks nicer to do
        if inter.data.resolved.members and len(inter.data.resolved.members.keys()) == 1:
            victim_str = tuple(inter.data.resolved.members.values())[0].display_name
        elif inter.data.resolved.users and len(inter.data.resolved.users.keys()) == 1:
            victim_str = tuple(inter.data.resolved.users.values())[0].display_name
        else:
            victim_str = discord.utils.escape_markdown(target)
        victim_str = f"**{victim_str}**"

        author_str = f"**{inter.author.display_name}**"

        kill_msg = random.choice(self.bot.death_messages)
        kill_msg = kill_msg.replace("%1$s", victim_str)
        kill_msg = kill_msg.replace("%2$s", author_str)
        kill_msg = kill_msg.replace("%3$s", "*Seraphim*")
        kill_msg = f"{kill_msg}."

        kill_embed = discord.Embed(colour=discord.Colour.red(), description=kill_msg)
        await inter.reply(embed=kill_embed)

    def error_embed_generate(self, error_msg):
        return discord.Embed(colour=discord.Colour.red(), description=error_msg)

    @commands.Cog.listener()
    async def on_slash_command_error(
        self, inter: dislash.SlashInteraction, error: dislash.ApplicationCommandError
    ):
        if isinstance(
            error,
            (
                dislash.BadArgument,
                dislash.InteractionCheckFailure,
                dislash.NotGuildOwner,
            ),
        ):
            await inter.reply(
                embed=self.error_embed_generate(str(error)), ephemeral=True
            )
        elif "Unknown interaction" in str(error):
            await inter.channel.send(
                f"{inter.author.mention}, the bot is a bit slow and so cannot do slash commands right now. Please wait a bit and try again.",
                delete_after=3,
            )
        else:
            await utils.error_handle(self.bot, error, inter)


def setup(bot):
    importlib.reload(utils)
    bot.add_cog(SlashCMDS(bot))
