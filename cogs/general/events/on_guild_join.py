#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib, math

import bot_utils.universals as univ

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

def setup(bot):
    bot.add_cog(OnGuildJoin(bot))