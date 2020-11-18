from discord.ext import commands
import importlib, discord

import common.star_mes_handler as star_mes
import common.classes as custom_classes

class SnipeEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.system_content != "":
            if not message.channel.id in self.bot.snipes["deletes"].keys():
                self.bot.snipes["deletes"][message.channel.id] = []
            
            snipe_embed = await star_mes.base_generate(self.bot, message, no_attachments=True)
            snipe_embed.color = discord.Colour(0x4378fc)
            self.bot.snipes["deletes"][message.channel.id].append(custom_classes.SnipedMessage(snipe_embed))

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.system_content != after.system_content:
            if before.system_content != "":
                if not before.channel.id in self.bot.snipes["edits"].keys():
                    self.bot.snipes["edits"][before.channel.id] = []

                snipe_embed = await star_mes.base_generate(self.bot, before, no_attachments=True)
                snipe_embed.color = discord.Colour(0x4378fc)
                self.bot.snipes["edits"][before.channel.id].append(custom_classes.SnipedMessage(snipe_embed))

def setup(bot):
    importlib.reload(star_mes)
    importlib.reload(custom_classes)
    bot.add_cog(SnipeEvents(bot))