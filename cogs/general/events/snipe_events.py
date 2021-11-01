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
    async def on_message_delete(self, message):
        if message.system_content != "":
            if message.channel.id not in self.bot.snipes["deletes"].keys():
                self.bot.snipes["deletes"][message.channel.id] = []

            try:
                snipe_embed = await star_mes.base_generate(
                    self.bot, message, no_attachments=True
                )
            except discord.InvalidArgument:
                return

            snipe_embed.color = discord.Colour(0x4378FC)
            snipe_embed.set_footer(text=f"Author ID: {message.author.id}")
            self.bot.snipes["deletes"][message.channel.id].append(
                custom_classes.SnipedMessage(snipe_embed)
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.system_content == after.system_content:
            return

        if before.system_content != "":
            if before.channel.id not in self.bot.snipes["edits"].keys():
                self.bot.snipes["edits"][before.channel.id] = []

            try:
                snipe_embed = await star_mes.base_generate(
                    self.bot, before, no_attachments=True
                )
            except discord.InvalidArgument:
                return

            snipe_embed.color = discord.Colour(0x4378FC)
            snipe_embed.set_footer(text=f"Author ID: {before.author.id}")
            self.bot.snipes["edits"][before.channel.id].append(
                custom_classes.SnipedMessage(snipe_embed)
            )


def setup(bot):
    importlib.reload(star_mes)
    importlib.reload(custom_classes)
    bot.add_cog(SnipeEvents(bot))
