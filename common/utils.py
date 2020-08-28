#!/usr/bin/env python3.7
from discord.ext import commands
import traceback, discord, datetime
import collections, os
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
    error_str = error_format(error)

    await msg_to_owner(bot, error_str)

    if ctx != None:
        await ctx.send("An internal error has occured. The bot owner has been notified.")

async def msg_to_owner(bot, content):
    # sends a message to the owner
    owner = bot.owner
    string = str(content)

    str_chunks = string_split(string)

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

def generate_mentions(ctx: commands.Context):
    # generates an AllowedMentions object that is similar to what a user can usually use

    permissions = ctx.author.guild_permissions
    # i assume mention_everyone also means they can ping all roles
    can_mention = (permissions.administrator or permissions.mention_everyone
    or ctx.guild.owner.id == ctx.author.id)

    if can_mention:
        # i could use a default AllowedMentions object, but this is more clear
        return discord.AllowedMentions(everyone=True, users=True, roles=True)
    else:
        pingable_roles = [r for r in ctx.guild.roles if r.mentionable]
        return discord.AllowedMentions(everyone=False, users=True, roles=pingable_roles)

def error_format(error):
    # simple function that formats an exception
    return ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))

def string_split(string):
    # simple function that splits a string into 1950-character parts
    return [string[i:i+1950] for i in range(0, len(string), 1950)]

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

def get_content(message: discord.Message):
    """Because system_content isn't perfect.
    More or less a copy of system_content with name being swapped with display_name."""

    if message.type is discord.MessageType.default:
        return message.content

    if message.type is discord.MessageType.pins_add:
        return '{0.display_name} pinned a message to this channel.'.format(message.author)

    if message.type is discord.MessageType.new_member:
        formats = [
            "{0} joined the party.",
            "{0} is here.",
            "Welcome, {0}. We hope you brought pizza.",
            "A wild {0} appeared.",
            "{0} just landed.",
            "{0} just slid into the server.",
            "{0} just showed up!",
            "Welcome {0}. Say hi!",
            "{0} hopped into the server.",
            "Everyone welcome {0}!",
            "Glad you're here, {0}.",
            "Good to see you, {0}.",
            "Yay you made it, {0}!",
        ]

        # manually reconstruct the epoch with millisecond precision, because
        # datetime.datetime.timestamp() doesn't return the exact posix
        # timestamp with the precision that we need
        created_at_ms = int((message.created_at - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
        return formats[created_at_ms % len(formats)].format(message.author.display_name)

    if message.type is discord.MessageType.premium_guild_subscription:
        return '{0.author.display_name} just boosted the server!'.format(message)

    if message.type is discord.MessageType.premium_guild_tier_1:
        return '{0.author.display_name} just boosted the server! {0.guild} has achieved **Level 1!**'.format(message)

    if message.type is discord.MessageType.premium_guild_tier_2:
        return '{0.author.display_name} just boosted the server! {0.guild} has achieved **Level 2!**'.format(message)

    if message.type is discord.MessageType.premium_guild_tier_3:
        return '{0.author.display_name} just boosted the server! {0.guild} has achieved **Level 3!**'.format(message)

    if message.type is discord.MessageType.channel_follow_add:
        return '{0.author.display_name} has added {0.content} to this channel'.format(message)

    else:
        raise discord.InvalidArgument("This message has an invalid type!")

class CustomCheckFailure(commands.CheckFailure):
    # custom classs for custom prerequisite failures outside of normal command checks
    # this class is so minor i'm not going to bother to migrate it to classes.py
    pass