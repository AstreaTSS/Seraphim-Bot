#!/usr/bin/env python3.7
import discord, os, asyncio
import websockets, logging
from discord.ext import commands
from datetime import datetime

import common.utils as utils

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(filename=os.environ.get("LOG_FILE_PATH"), level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s")

def seraphim_prefixes(bot: commands.Bot, msg: discord.Message):
    # rn this is more or less when_mentioned_or('s!'), but soon this will be expanded for custom prefixes

    mention_prefixes = [f"{bot.user.mention} ", f"<@!{bot.user.id}> "]
    custom_prefixes = ["s!"]

    return mention_prefixes + custom_prefixes

# i plan on this being a custom class that inherits from commands.Bot
# instead of just being commands.Bot one day for custom processing of commands, but rn this works
bot = commands.Bot(command_prefix=seraphim_prefixes, fetch_offline_members=True)

@bot.event
async def on_ready():

    if bot.init_load == True:
        bot.starboard = {}
        bot.config = {}

        bot.snipes = {
            "deletes": {},
            "edits": {}
        }

        bot.star_queue = {}
        bot.star_lock = False

        image_endings = ("jpg", "jpeg", "png", "gif")
        bot.image_extensions = tuple(image_endings) # no idea why I have to do this

        application = await bot.application_info()
        bot.owner = application.owner

        bot.load_extension("cogs.db_handler")
        while bot.config == {}:
            await asyncio.sleep(0.1)

        cogs_list = utils.get_all_extensions(os.environ.get("DIRECTORY_OF_FILE"))

        for cog in cogs_list:
            if cog != "cogs.db_handler":
                try:
                    bot.load_extension(cog)
                except commands.NoEntryPointError:
                    pass

    utcnow = datetime.utcnow()
    time_format = utcnow.strftime("%x %X UTC")

    application = await bot.application_info()
    owner = application.owner

    connect_msg = f"Logged in at `{time_format}`!" if bot.init_load == True else f"Reconnected at `{time_format}`!"
    await owner.send(connect_msg)

    bot.init_load = False

    activity = discord.Activity(name = 'over a couple of servers', type = discord.ActivityType.watching)

    try:
        await bot.change_presence(activity = activity)
    except websockets.ConnectionClosedOK:
        await utils.msg_to_owner(bot, "Reconnecting...")

@bot.event
async def on_resumed():
    activity = discord.Activity(name = 'over a couple of servers', type = discord.ActivityType.watching)
    await bot.change_presence(activity = activity)

@bot.event
async def on_error(event, *args, **kwargs):
    try:
        raise
    except BaseException as e:
        await utils.error_handle(bot, e)

@bot.check
async def block_dms(ctx):
    return ctx.guild is not None

bot.init_load = True
bot.run(os.environ.get("MAIN_TOKEN"))