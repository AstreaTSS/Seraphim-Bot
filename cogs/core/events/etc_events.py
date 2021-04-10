#!/usr/bin/env python3.8
import datetime

import discord
from discord.ext import commands, tasks


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

        self.bot.remove_member(member)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.bot.update_member(member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        self.bot.update_member(after)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        for guild_id in self.bot.custom_cache.keys():
            if self.bot.custom_cache[guild_id].get(after.id) != None:
                guild = self.bot.get_guild(guild_id)
                if guild:
                    member = guild.get_member(after.id)
                    if member:
                        self.bot.update_member(member)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.custom_cache[guild.id] = {}
        for member in guild.members:
            self.bot.update_member(member)


def setup(bot):
    bot.add_cog(EtcEvents(bot))
