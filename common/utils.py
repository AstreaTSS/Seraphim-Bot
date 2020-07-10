#!/usr/bin/env python3.6
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
import traceback, discord, datetime, re, aiohttp
from pathlib import Path

async def proper_permissions(ctx):
    permissions = ctx.author.guild_permissions
    return (permissions.administrator or permissions.manage_guild)

async def fetch_needed(bot, payload):
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    channel = bot.get_channel(payload.channel_id)
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

    str_chunks = [string[i:i+1950] for i in range(0, len(string), 1950)]

    for chunk in str_chunks:
        await owner.send(f"{chunk}")

async def user_from_id(bot, guild, user_id):
    user = guild.get_member(user_id)
    if user == None:
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            user = None

    return user

async def type_from_url(url, bot = None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            
            data = await resp.content.read(12)
            tup_data = tuple(data)
            
            # first 7 bytes of most pngs
            png_list = (0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
            if tup_data[:8] == png_list:
                return "png"
            
            # first 12 bytes of most jp(e)gs. EXIF is a bit wierd, and so some manipulating had to be done
            jfif_list = (0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01)
            exif_lists = ((0xFF, 0xD8, 0xFF, 0xE1), (0x45, 0x78, 0x69, 0x66, 0x00, 0x00))

            if tup_data == jfif_list or (tup_data[:4] == exif_lists[0] and tup_data[6:] == exif_lists[1]):
                return "jpg"

            # first 6 bytes of most gifs. last two can be different, so we have to handle that
            gif_lists = ((0x47, 0x49, 0x46, 0x38), ((0x37, 0x61), (0x39, 0x61)))
            if tup_data[:4] == gif_lists[0] and tup_data[4:6] in gif_lists[1]:
                return "gif"

            # first 12 bytes of most webps. middle four are file size, so we ignore that
            # webp isnt actually used for anything bot-wise, just here for the sake of it
            webp_lists = ((0x52, 0x49, 0x46, 0x46), (0x57, 0x45, 0x42, 0x50))
            if tup_data[:4] == webp_lists[0] and tup_data[8:] == webp_lists[1]:
                return "webp"

    return None

def file_to_ext(str_path, base_path):
    str_path = str_path.replace(base_path, "")
    str_path = str_path.replace("/", ".")
    return str_path.replace(".py", "")

def get_all_extensions(str_path, folder = "cogs"):
    ext_files = []
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
    regex = re.compile(r"([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[eE]([+-]?\d+))?")

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
            time_value_list.append(float(match.group()))

        for entry in self.regex.split(argument):
            if not (entry == "" or entry == None):
                try:
                    float(entry)
                    continue
                except ValueError:
                    time_format_list.append(entry.strip().lower())

        if (time_format_list == [] or time_value_list == [] 
            or len(time_format_list) != len(time_value_list)):
            raise BadArgument(f"1. Argument {argument} is not a valid time duration.")

        for i in range(len(time_format_list)):
            if time_span == -1:
                time_span = 0

            time_span += self.to_seconds(time_value_list[i], time_format_list[i])

        if time_span == -1:
            raise BadArgument(f"2. Argument {argument} is not a valid time duration.")

        return datetime.timedelta(seconds=time_span)