#!/usr/bin/env python3.7
import traceback, discord
from pathlib import Path

async def proper_permissions(ctx):
    permissions = ctx.author.guild_permissions
    return (permissions.administrator or permissions.manage_messages)

async def fetch_needed(bot, payload):
    guild = await bot.fetch_guild(payload.guild_id)
    user = await guild.fetch_member(payload.user_id)

    channel = await bot.fetch_channel(payload.channel_id)
    mes = await channel.fetch_message(payload.message_id)

    return user, channel, mes

async def error_handle(bot, error, ctx = None):
    error_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))

    await msg_to_owner(bot, error_str)

    if ctx != None:
        await ctx.send("An internal error has occured. The bot owner has been notified.")

async def msg_to_owner(bot, string):
    application = await bot.application_info()
    owner = application.owner
    await owner.send(f"{string}")

async def user_from_id(bot, guild, user_id):
    user = guild.get_member(user_id)
    if user == None:
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            user = None

    return user

def file_to_ext(str_path, start_path):
    str_path = str_path.replace(start_path, "")
    str_path = str_path.replace("/", ".")
    return str_path.replace(".py", "")

def get_all_extensions(filename):
    ext_files = []
    loc_split = filename.split("cogs")
    start_path = loc_split[0]

    if start_path == filename:
        start_path = start_path.replace("main.py", "")
    start_path = start_path.replace("\\", "/")

    if start_path[-1] != "/":
        start_path += "/"

    pathlist = Path(f"{start_path}/cogs").glob('**/*.py')
    for path in pathlist:
        str_path = str(path.as_posix())
        str_path = file_to_ext(str_path, start_path)

        if str_path != "cogs.db_handler":
            ext_files.append(str_path)

    return ext_files