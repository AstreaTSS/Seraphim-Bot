#!/usr/bin/env python3.6
import discord, os, asyncio
import websockets
from discord.ext import commands
from datetime import datetime

import common.utils as utils

from dotenv import load_dotenv
load_dotenv()

bot = commands.Bot(command_prefix=commands.when_mentioned_or("s!"), fetch_offline_members=True)

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

        bot.load_extension("cogs.db_handler")
        while bot.config == {}:
            await asyncio.sleep(0.1)

        cogs_list = ['cogs.core.cmds.cog_control', 'cogs.core.cmds.eval_cmd', 'cogs.core.cmds.help_cmd', 'cogs.core.cmds.norm_cmds', 
        'cogs.core.events.etc_events', 'cogs.core.events.on_cmd_error', 
        'cogs.core.settings.settings', 'cogs.general.cmds.ping_role_cmds', 'cogs.general.cmds.pin_cmds', 
        'cogs.general.cmds.say_cmds', 'cogs.general.cmds.snipe_cmds', 'cogs.general.events.pin_handle', 'cogs.starboard.clear_events', 
        'cogs.starboard.star_cmds', 'cogs.starboard.star_handling']

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