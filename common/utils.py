#!/usr/bin/env python3.7
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
import traceback, discord, datetime
import re, collections, os
from pathlib import Path

async def proper_permissions(ctx):
    # checks if author has admin or manage guild perms or is the owner
    permissions = ctx.author.guild_permissions
    return (permissions.administrator or permissions.manage_guild
    or ctx.guild.owner.id == ctx.author.id)

async def fetch_needed(bot, payload):
    # fetches info from payload
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    channel = bot.get_channel(payload.channel_id)
    mes = await channel.fetch_message(payload.message_id)

    return user, channel, mes

async def error_handle(bot, error, ctx = None):
    # handles errors and sends them to owner
    error_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))

    await msg_to_owner(bot, error_str)

    if ctx != None:
        await ctx.send("An internal error has occured. The bot owner has been notified.")

async def msg_to_owner(bot, content):
    # sends a message to the owner
    owner = bot.owner
    string = str(content)

    str_chunks = [string[i:i+1950] for i in range(0, len(string), 1950)]

    for chunk in str_chunks:
        await owner.send(f"{chunk}")

async def user_from_id(bot, guild, user_id):
    # gets a user from id. attempts via guild first, then attempts globally
    user = guild.get_member(user_id) # member in guild
    if user == None:
        user = bot.get_user(user_id) # user in cache
        
        if user == None:
            try:
                user = await bot.fetch_user(user_id) # a user that exists
            except discord.NotFound:
                user = None

    return user

def file_to_ext(str_path, base_path):
    # changes a file to an import-like string
    str_path = str_path.replace(base_path, "")
    str_path = str_path.replace("/", ".")
    return str_path.replace(".py", "")

def get_all_extensions(str_path, folder = "cogs"):
    # gets all extensions in a folder
    ext_files = collections.deque()
    loc_split = str_path.split("cogs")
    base_path = loc_split[0]

    if base_path == str_path:
        base_path = base_path.replace("main.py", "")
    base_path = base_path.replace("\\", "/")

    if base_path[-1] != "/":
        base_path += "/"

    pathlist = Path(f"{base_path}/{folder}").glob('**/*.py')
    for path in pathlist:
        str_path = str(path.as_posix())
        str_path = file_to_ext(str_path, base_path)

        if str_path != "cogs.db_handler":
            ext_files.append(str_path)

    return ext_files

def chan_perm_check(channel: discord.TextChannel, perms: discord.Permissions):
    # checks if bot can do what it needs to do in a channel
    resp = "OK"

    if not perms.read_messages:
        resp = f"I cannot read messages in {channel.mention}!"
    elif not perms.read_message_history:
        resp = f"I cannot read the message history in {channel.mention}!"
    elif not perms.send_messages:
        resp = f"I cannot send messages in {channel.mention}!"
    elif not perms.embed_links:
        resp = f"I cannot send embeds in {channel.mention}!"

    return resp

class CustomCheckFailure(commands.CheckFailure):
    # custom classs for custom prerequisite failures outside of normal command checks
    pass

class TimeDurationConverter(commands.Converter):
    # Converts a string to a time duration.

    convert_dict = {
        "s": 1,
        "second": 1,
        "seconds": 1,

        "m": 60, # s * 60
        "minute": 60,
        "minutes": 60,

        "h": 3600, # m * 60
        "hour": 3600,
        "hours": 3600,

        "d": 86400, # h * 24
        "day": 86400,
        "days": 86400,

        "mo": 2592000, # d * 30
        "month": 2592000,
        "months": 2592000,

        "y": 31536000, # d * 365
        "year": 31536000,
        "years": 31536000
    }
    regex = re.compile(r"([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[eE]([+-]?\d+))?") # splits character and number

    def to_seconds(self, time_value, time_prefix):
        try:
            return self.convert_dict[time_prefix] * time_value
        except KeyError:
            raise BadArgument(f"{time_prefix} is not a valid time prefix.")

    async def convert(self, ctx, argument):
        time_value_list = []
        time_format_list = []
        time_span = -1

        for match in self.regex.finditer(argument):
            time_value_list.append(float(match.group())) # gets number value

        for entry in self.regex.split(argument):
            if not (entry == "" or entry == None):
                try:
                    float(entry)
                    continue
                except ValueError:
                    time_format_list.append(entry.strip().lower()) # gets h, m, s, etc.

        if (time_format_list == [] or time_value_list == [] 
            or len(time_format_list) != len(time_value_list)):
            raise BadArgument(f"Argument {argument} is not a valid time duration.")

        for i in range(len(time_format_list)):
            if time_span == -1:
                time_span = 0

            time_span += self.to_seconds(time_value_list[i], time_format_list[i])

        if time_span == -1:
            raise BadArgument(f"Argument {argument} is not a valid time duration.")

        return datetime.timedelta(seconds=time_span)