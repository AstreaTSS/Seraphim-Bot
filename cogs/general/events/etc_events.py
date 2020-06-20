#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import discord, importlib, datetime

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

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if not guild.id in list(self.bot.config.keys()):
            self.bot.config[guild.id] = {
                "starboard_id": None,
                "star_limit": None,
                "star_blacklist": [],
                "star_toggle": False,
                "pingable_roles": {},

                "guild_id_bac": guild.id
            }

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.content != "":
            now = datetime.datetime.utcnow()
            self.bot.sniped[message.channel.id] = {
                "author": message.author,
                "content": message.content,
                "created_at": message.created_at,
                "time_deleted": now
            }

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            if before.content != "":
                now = datetime.datetime.utcnow()
                self.bot.editsniped[before.channel.id] = {
                    "author": before.author,
                    "content": before.content,
                    "created_at": before.created_at,
                    "time_edited": now
                }

def setup(bot):
    bot.add_cog(EtcEvents(bot))