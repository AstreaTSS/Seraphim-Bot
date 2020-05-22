#!/usr/bin/env python3.7
import discord, os, asyncio
from discord.ext import commands
import logging, time, math
from datetime import datetime
import star_utils.universals as univ

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename=os.environ.get("LOG_PATH"), encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler.formatter.converter = time.gmtime
logger.addHandler(handler)

async def _prefix(bot, msg):
    bot_id = bot.user.id
    return [f"<@{bot_id}> ", f"<@!{bot_id}> ", "s!"]

bot = commands.Bot(command_prefix=_prefix, fetch_offline_members=True)

bot.remove_command("help")

@bot.event
async def on_ready():

    if bot.on_readies == 0:
        bot.starboard = {}
        bot.star_config = {}
        bot.logger = logger
        bot.load_extension("cogs.db_handler")
        while bot.star_config == {}:
            await asyncio.sleep(0.1)

        cogs_list = ["cogs.events.star_handling", "cogs.events.clear_events", "cogs.cmds.norm_cmds", "cogs.cmds.admin_cmds",
        "cogs.cmds.blacklist_cmds", "cogs.cmds.owner_cmds"]

        for cog in cogs_list:
            bot.load_extension(cog)

    utcnow = datetime.utcnow()
    time_format = utcnow.strftime("%x %X UTC")

    application = await bot.application_info()
    owner = application.owner

    connect_msg = f"Logged in at `{time_format}`!" if bot.on_readies == 0 else f"Reconnected at `{time_format}`!"

    await owner.send(connect_msg)
    activity = discord.Activity(name = 'for stars!', type = discord.ActivityType.watching)
    await bot.change_presence(activity = activity)

    bot.on_readies += 1
        
@bot.check
async def block_dms(ctx):
    return ctx.guild is not None

@bot.event
async def on_error(event, *args, **kwargs):
    try:
        raise
    except Exception as e:
        await univ.error_handle(bot, e)
        
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        if not isinstance(original, discord.HTTPException):
            await univ.error_handle(bot, error)
    elif isinstance(error, (commands.ConversionError, commands.UserInputError)):
        await ctx.send(error)
    elif isinstance(error, commands.CheckFailure):
        if ctx.guild != None:
            await ctx.send("You do not have the proper permissions to use that command.")
    elif isinstance(error, commands.CommandOnCooldown):
        time_to_wait = math.ceil(error.retry_after)
        await ctx.send(f"You're doing that command too fast! Try again after {time_to_wait} seconds.")
    elif isinstance(error, commands.CommandNotFound):
        ignore = True
    else:
        await univ.error_handle(bot, error)

bot.on_readies = 0
bot.run(os.environ.get("MAIN_TOKEN"))