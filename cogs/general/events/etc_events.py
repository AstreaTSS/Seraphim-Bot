#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib, datetime

class OnGuildJoin(commands.Cog):
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

                "guild_id_bac": guild.id
            }

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        now = datetime.datetime.utcnow()
        self.bot.sniped[message.channel.id] = {
            "id": message.id,
            "author": message.author,
            "content": message.content,
            "created_at": message.created_at,
            "time_deleted": now
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            now = datetime.datetime.utcnow()
            self.bot.editsniped[before.channel.id] = {
                "id": before.id,
                "author": before.author,
                "content": before.content,
                "created_at": before.created_at,
                "time_edited": now
            }

def setup(bot):
    bot.add_cog(OnGuildJoin(bot))