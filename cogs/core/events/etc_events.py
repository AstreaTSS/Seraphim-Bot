#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import datetime

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
        if not member.id in self.bot.role_rolebacks.keys():
            self.bot.role_rolebacks[member.id] = {
                "roles": member.roles, 
                "time": datetime.datetime.utcnow(),
                "id": member.id
            }

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if not guild.id in list(self.bot.config.keys()):
            # TODO: make starboard into it's own sub category
            self.bot.config[guild.id] = {
                "starboard_id": None,
                "star_limit": None,
                "star_blacklist": [],
                "star_toggle": False,
                "remove_reaction": False,
                "pingable_roles": {},
                "pin_config": {},
                "prefixes": ["s!"],
                "disables": {
                    "users": {},
                    "channels": {}
                },

                "guild_id_bac": guild.id
            }
            
def setup(bot):
    bot.add_cog(EtcEvents(bot))