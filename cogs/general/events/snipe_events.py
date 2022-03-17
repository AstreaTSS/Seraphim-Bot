import importlib

import discord
from discord.ext import commands

import common.classes as custom_classes
import common.star_mes_handler as star_mes
import common.utils as utils


class SnipeEvents(commands.Cog):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.system_content != "" and message.guild:
            if message.channel.id not in self.bot.snipes["deletes"].keys():
                self.bot.snipes["deletes"][message.channel.id] = []

            try:
                snipe_embed = await star_mes.base_generate(
                    self.bot, message, no_attachments=True
                )
            except discord.InvalidArgument:
                return

            snipe_embed.color = discord.Colour(0x4378FC)
            new_url = f"{snipe_embed.author.icon_url}&userid={message.author.id}"
            snipe_embed.set_author(name=snipe_embed.author.name, icon_url=new_url)
            self.bot.snipes["deletes"][message.channel.id].append(
                custom_classes.SnipedMessage(embed=snipe_embed)
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.system_content == after.system_content:
            return

        if before.system_content != "" and before.guild:
            if before.channel.id not in self.bot.snipes["edits"].keys():
                self.bot.snipes["edits"][before.channel.id] = []

            try:
                snipe_embed = await star_mes.base_generate(
                    self.bot, before, no_attachments=True
                )
            except discord.InvalidArgument:
                return

            snipe_embed.color = discord.Colour(0x4378FC)
            new_url = f"{snipe_embed.author.icon_url}&userid={before.author.id}"
            snipe_embed.set_author(name=snipe_embed.author.name, icon_url=new_url)
            self.bot.snipes["edits"][before.channel.id].append(
                custom_classes.SnipedMessage(embed=snipe_embed)
            )


async def setup(bot):
    importlib.reload(star_mes)
    importlib.reload(custom_classes)
    await bot.add_cog(SnipeEvents(bot))
