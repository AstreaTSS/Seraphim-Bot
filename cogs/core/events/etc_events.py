#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import discord, datetime, asyncio, traceback

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
        error_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))

        application = await self.bot.application_info()
        owner = application.owner

        str_chunks = [error_str[i:i+1950] for i in range(0, len(error_str), 1950)]

        for chunk in str_chunks:
            await owner.send(f"{chunk}")


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
        if message.content != "":
            now = datetime.datetime.utcnow()
            if not message.channel.id in self.bot.snipes["deletes"].keys():
                self.bot.snipes["deletes"][message.channel.id] = []

            self.bot.snipes["deletes"][message.channel.id].append({
                "mes": message,
                "time_deleted": now
            })

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            if before.content != "":
                now = datetime.datetime.utcnow()
                if not before.channel.id in self.bot.snipes["edits"].keys():
                    self.bot.snipes["edits"][before.channel.id] = []
                
                self.bot.snipes["edits"][before.channel.id].append({
                    "mes": before,
                    "time_edited": now
                })

def setup(bot):
    bot.add_cog(EtcEvents(bot))