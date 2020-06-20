#!/usr/bin/env python3.7
import discord, os, asyncio
from discord.ext import commands
from datetime import datetime

import bot_utils.universals as univ

from dotenv import load_dotenv
load_dotenv()

async def _prefix(bot, msg):
    bot_id = bot.user.id
    return [f"<@{bot_id}> ", f"<@!{bot_id}> ", "s!"]

bot = commands.Bot(command_prefix=_prefix, fetch_offline_members=True)

bot.remove_command("help")

@bot.event
async def on_ready():

    if bot.init_load == True:
        bot.starboard = {}
        bot.config = {}

        bot.sniped = {}
        bot.editsniped = {}

        bot.star_queue = {}

        bot.load_extension("cogs.db_handler")
        while bot.config == {}:
            await asyncio.sleep(0.1)

        cogs_list = univ.get_all_extensions(os.environ.get("DIRECTORY_OF_FILE"))

        for cog in cogs_list:
            if cog != "cogs.db_handler":
                bot.load_extension(cog)

        activity = discord.Activity(name = 'over a couple of servers', type = discord.ActivityType.watching)
        await bot.change_presence(activity = activity)

    utcnow = datetime.utcnow()
    time_format = utcnow.strftime("%x %X UTC")

    application = await bot.application_info()
    owner = application.owner

    connect_msg = f"Logged in at `{time_format}`!" if bot.init_load == True else f"Reconnected at `{time_format}`!"
    await owner.send(connect_msg)

    bot.init_load = False

@bot.event
async def on_error(event, *args, **kwargs):
    try:
        raise
    except Exception as e:
        await univ.error_handle(bot, e)

@bot.check
async def block_dms(ctx):
    return ctx.guild is not None

bot.init_load = True
bot.run(os.environ.get("MAIN_TOKEN"))