#!/usr/bin/env python3.8
import datetime

import discord
from discord.ext import commands
from discord.ext import tasks


class EtcEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.rollback_roles_cleanup.start()

    async def cog_unload(self):
        self.rollback_roles_cleanup.cancel()

    @tasks.loop(minutes=7.5)
    async def rollback_roles_cleanup(self):
        now = discord.utils.utcnow()
        hour_prior = now - datetime.timedelta(hours=1)

        for member_entry in list(self.bot.role_rolebacks.values()):
            if member_entry["time"] < hour_prior:
                del self.bot.role_rolebacks[member_entry["id"]]

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_entry = self.bot.role_rolebacks.get(member.guild.id)

        if not guild_entry:
            self.bot.role_rolebacks[member.guild.id] = {}
            guild_entry = {}

        self.bot.role_rolebacks[member.guild.id][member.id] = {
            "roles": member.roles,
            "time": discord.utils.utcnow(),
            "id": member.id,
        }


async def setup(bot):
    await bot.add_cog(EtcEvents(bot))
