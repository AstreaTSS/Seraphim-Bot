#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import discord, datetime
import asyncio, importlib

import common.utils as utils
import common.classes as custom_classes

class EtcEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if not guild.id in list(self.bot.config.keys()):
            self.bot.config[guild.id] = {
                "starboard_id": None,
                "star_limit": None,
                "star_blacklist": [],
                "star_toggle": False,
                "pingable_roles": {},
                "pin_config": {},

                "guild_id_bac": guild.id
            }

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.system_content != "":
            now = datetime.datetime.utcnow()
            if not message.channel.id in self.bot.snipes["deletes"].keys():
                self.bot.snipes["deletes"][message.channel.id] = []
            
            self.bot.snipes["deletes"][message.channel.id].append(custom_classes.SnipedMessage(message, now))

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.system_content != after.system_content:
            if before.system_content != "":
                now = datetime.datetime.utcnow()
                if not before.channel.id in self.bot.snipes["edits"].keys():
                    self.bot.snipes["edits"][before.channel.id] = []
                
                self.bot.snipes["edits"][before.channel.id].append(custom_classes.SnipedMessage(before, now))

def setup(bot):
    importlib.reload(utils)
    importlib.reload(custom_classes)
    bot.add_cog(EtcEvents(bot))