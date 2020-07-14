#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import discord, datetime
import asyncio, importlib

import common.utils as utils

class EtcEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activity_refresh.start()

    def cog_unload(self):
        self.activity_refresh.cancel()

    @tasks.loop(hours=2.5)
    async def activity_refresh(self):
        activity = discord.Activity(name = 'over a couple of servers', type = discord.ActivityType.watching)
        await self.bot.change_presence(activity = activity)

    @activity_refresh.error
    async def error_handle(self, *args):
        error = args[-1]
        await utils.error_handle(self.bot, error)

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

            self.bot.snipes["deletes"][message.channel.id].append({
                "author_name": f"{message.author.display_name} ({str(message.author)})",
                "author_url": str(message.author.avatar_url_as(format=None,static_format='jpg', size=128)),
                "mes_content": message.system_content,
                "created_at": message.created_at,
                "time_deleted": now
            })

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.system_content != after.system_content:
            if before.system_content != "":
                now = datetime.datetime.utcnow()
                if not before.channel.id in self.bot.snipes["edits"].keys():
                    self.bot.snipes["edits"][before.channel.id] = []
                
                self.bot.snipes["edits"][before.channel.id].append({
                    "author_name": f"{before.author.display_name} ({str(before.author)})",
                    "author_url": str(before.author.avatar_url_as(format=None,static_format='jpg', size=128)),
                    "mes_content": before.system_content,
                    "created_at": before.created_at,
                    "time_edited": now
                })

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(EtcEvents(bot))