#!/usr/bin/env python3.8
import datetime

import discord
from discord.ext import commands
from discord.ext import tasks


class EtcEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=7.5)
    async def rollback_roles_cleanup(self):
        now = datetime.datetime.utcnow()
        fifteen_prior = now - datetime.timedelta(minutes=15)

        for member_entry in list(self.bot.role_rolebacks.values()):
            if member_entry["time"] < fifteen_prior:
                del self.bot.role_rolebacks[member_entry["id"]]

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_entry = self.bot.role_rolebacks.get(member.guild.id)

        if not guild_entry:
            self.bot.role_rolebacks[member.guild.id] = {}
            guild_entry = {}

        if not member.id in guild_entry.keys():
            self.bot.role_rolebacks[member.guild.id][member.id] = {
                "roles": member.roles,
                "time": datetime.datetime.utcnow(),
                "id": member.id,
            }


def setup(bot):
    bot.add_cog(EtcEvents(bot))
