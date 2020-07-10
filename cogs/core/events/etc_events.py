#!/usr/bin/env python3.6
from discord.ext import commands, tasks
import discord, datetime, importlib, io

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
        if message.content != "" or message.attachments != []:
            now = datetime.datetime.utcnow()
            if not message.channel.id in self.bot.snipes["deletes"].keys():
                self.bot.snipes["deletes"][message.channel.id] = []

            image = None
            img_file_type = None

            if message.attachments != []:
                image_endings = ("jpg", "png", "gif")
                image_extensions = tuple(image_endings) # no idea why I have to do this

                file_type = await utils.type_from_url(message.attachments[0].proxy_url)
                if file_type in image_extensions:
                    try:
                        image = io.BytesIO(await message.attachments[0].read(use_cached=True))
                        img_file_type = file_type
                    except discord.NotFound:
                        if message.content == "":
                            return
                elif message.content == "":
                    return

            self.bot.snipes["deletes"][message.channel.id].append({
                "mes": message,
                "image": image,
                "file_type": img_file_type,
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
                    "image": None,
                    "time_edited": now
                })

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(EtcEvents(bot))