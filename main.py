#!/usr/bin/env python3.7
import discord, os, asyncio
from discord.ext import commands
import logging, time, traceback
from datetime import datetime

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

async def error_handle(bot, error):
    error_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))

    application = await bot.application_info()
    owner = application.owner
    await owner.send(f"{error_str}")

    logger.error(error_str)

@bot.event
async def on_ready():
    bot.starboard = {}
    bot.star_config = {}
    bot.logger = logger
    bot.load_extension("cogs.db_handler")
    while bot.star_config == {} or bot.starboard == {}:
        await asyncio.sleep(0.1)

    cogs_list = ["cogs.star_handling", "cogs.clear_events", "cogs.commands"]

    for cog in cogs_list:
        bot.load_extension(cog)

    utcnow = datetime.utcnow()
    time_format = utcnow.strftime("%x %X UTC")

    application = await bot.application_info()
    owner = application.owner
    await owner.send(f"Logged in at `{time_format}`!")

    activity = discord.Activity(name = 'for stars!', type = discord.ActivityType.watching)
    await bot.change_presence(activity = activity)
    
@bot.check
async def block_dms(ctx):
    return ctx.guild is not None

@bot.event
async def on_error(event, *args, **kwargs):
    try:
        raise
    except Exception as e:
        await error_handle(bot, e)
        
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        if not isinstance(original, discord.HTTPException):
            await error_handle(bot, error)
    elif isinstance(error, (commands.ConversionError, commands.UserInputError)):
        await ctx.send(error)
    elif isinstance(error, commands.CheckFailure):
        if ctx.guild != None:
            await ctx.send("You do not have the proper permissions to use that command.")
    elif isinstance(error, commands.CommandNotFound):
        ignore = True
    else:
        await error_handle(bot, error)

bot.run(os.environ.get("MAIN_TOKEN"))