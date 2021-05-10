#!/usr/bin/env python3.8
import collections
import datetime
import logging
import os
import traceback
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands


async def proper_permissions(ctx: commands.Context):
    # checks if author has admin or manage guild perms or is the owner
    permissions = ctx.channel.permissions_for(ctx.author)
    return permissions.administrator or permissions.manage_guild


async def fetch_needed(bot, payload):
    # fetches info from payload
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if user is None:  # rare, but it's happened
        user = await guild.fetch_member(payload.user_id)

    channel = bot.get_channel(payload.channel_id)
    mes = await channel.fetch_message(payload.message_id)

    return user, channel, mes


async def error_handle(bot, error, ctx=None):
    # handles errors and sends them to owner
    if isinstance(error, aiohttp.ServerDisconnectedError):
        to_send = "Disconnected from server!"
        split = True
    else:
        error_str = error_format(error)
        logging.getLogger("discord").error(error_str)

        error_split = error_str.splitlines()
        chunks = [error_split[x : x + 20] for x in range(0, len(error_split), 20)]
        for i in range(len(chunks)):
            chunks[i][0] = f"```py\n{chunks[i][0]}"
            chunks[i][len(chunks[i]) - 1] += "\n```"

        final_chunks = []
        for chunk in chunks:
            final_chunks.append("\n".join(chunk))

        if ctx and hasattr(ctx, "message") and hasattr(ctx.message, "jump_url"):
            final_chunks.insert(0, f"Error on: {ctx.message.jump_url}")

        to_send = final_chunks
        split = False

    await msg_to_owner(bot, to_send, split)

    if ctx:
        if hasattr(ctx, "reply"):
            await ctx.reply(
                "An internal error has occured. The bot owner has been notified."
            )
        else:
            await ctx.channel.send(
                content="An internal error has occured. The bot owner has been notified."
            )


async def msg_to_owner(bot, content, split=True):
    # sends a message to the owner
    owner = bot.owner
    string = str(content)

    str_chunks = string_split(string) if split else content
    for chunk in str_chunks:
        await owner.send(f"{chunk}")


async def user_from_id(bot, guild, user_id):
    # gets a user from id. attempts via guild first, then attempts globally
    user = guild.get_member(user_id)  # member in guild
    if user is None:
        user = bot.get_user(user_id)  # user in cache

    if user is None:
        try:
            user = await bot.fetch_user(user_id)  # a user that exists
        except discord.NotFound:
            user = None

    return user


def embed_check(embed: discord.Embed) -> bool:
    """Checks if an embed is valid, as per Discord's guidelines.
    See https://discord.com/developers/docs/resources/channel#embed-limits for details."""
    if len(embed) > 6000:
        return False

    if embed.title and embed.title > 256:
        return False
    if embed.description and embed.description > 2048:
        return False
    if embed.author and embed.author.name and embed.author.name > 256:
        return False
    if embed.footer and embed.footer.text and embed.footer.text > 2048:
        return False
    if embed.fields:
        if len(embed.fields) > 25:
            return False
        for field in embed.fields:
            if field.name and field.name > 1024:
                return False
            if field.value and field.value > 2048:
                return False

    return True


def deny_mentions(user):
    # generates an AllowedMentions object that only pings the user specified
    return discord.AllowedMentions(everyone=False, users=[user], roles=False)


def generate_mentions(ctx: commands.Context):
    # sourcery skip: remove-unnecessary-else
    # generates an AllowedMentions object that is similar to what a user can usually use

    permissions = ctx.channel.permissions_for(ctx.author)
    can_mention = permissions.administrator or permissions.mention_everyone

    if can_mention:
        # i could use a default AllowedMentions object, but this is more clear
        return discord.AllowedMentions(everyone=True, users=True, roles=True)
    else:
        pingable_roles = tuple(r for r in ctx.guild.roles if r.mentionable)
        return discord.AllowedMentions(everyone=False, users=True, roles=pingable_roles)


def error_format(error):
    # simple function that formats an exception
    return "".join(
        traceback.format_exception(
            etype=type(error), value=error, tb=error.__traceback__
        )
    )


def string_split(string):
    # simple function that splits a string into 1950-character parts
    return [string[i : i + 1950] for i in range(0, len(string), 1950)]


def file_to_ext(str_path, base_path):
    # changes a file to an import-like string
    str_path = str_path.replace(base_path, "")
    str_path = str_path.replace("/", ".")
    return str_path.replace(".py", "")


def get_all_extensions(str_path, folder="cogs"):
    # gets all extensions in a folder
    ext_files = collections.deque()
    loc_split = str_path.split("cogs")
    base_path = loc_split[0]

    if base_path == str_path:
        base_path = base_path.replace("main.py", "")
    base_path = base_path.replace("\\", "/")

    if base_path[-1] != "/":
        base_path += "/"

    pathlist = Path(f"{base_path}/{folder}").glob("**/*.py")
    for path in pathlist:
        str_path = str(path.as_posix())
        str_path = file_to_ext(str_path, base_path)

        if str_path != "cogs.db_handler":
            ext_files.append(str_path)

    return ext_files


def get_content(message: discord.Message):
    """Because system_content isn't perfect.
    More or less a copy of system_content with name being swapped with display_name and DM message types removed."""

    if message.type is discord.MessageType.default:
        return message.content

    if message.type is discord.MessageType.pins_add:
        return "{0.display_name} pinned a message to this channel.".format(
            message.author
        )

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
        created_at_ms = int(
            (message.created_at - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
        )
        return formats[created_at_ms % len(formats)].format(message.author.display_name)

    if message.type is discord.MessageType.premium_guild_subscription:
        return f'{os.environ.get("BOOST_EMOJI_NAME")} {message.author.display_name} just boosted the server!'

    if message.type is discord.MessageType.premium_guild_tier_1:
        return f'{os.environ.get("BOOST_EMOJI_NAME")} {message.author.display_name} just boosted the server! {message.guild} has achieved **Level 1!**'

    if message.type is discord.MessageType.premium_guild_tier_2:
        return f'{os.environ.get("BOOST_EMOJI_NAME")} {message.author.display_name} just boosted the server! {message.guild} has achieved **Level 2!**'

    if message.type is discord.MessageType.premium_guild_tier_3:
        return f'{os.environ.get("BOOST_EMOJI_NAME")} {message.author.display_name} just boosted the server! {message.guild} has achieved **Level 3!**'

    if message.type is discord.MessageType.channel_follow_add:
        return "{0.author.display_name} has added {0.content} to this channel".format(
            message
        )

    if message.type is discord.MessageType.guild_stream:
        return "{0.author.display_name} is live! Now streaming {0.author.activity.name}".format(
            message
        )

    if message.type is discord.MessageType.guild_discovery_disqualified:
        return "This server has been removed from Server Discovery because it no longer passes all the requirements. Check Server Settings for more details."

    if message.type is discord.MessageType.guild_discovery_requalified:
        return "This server is eligible for Server Discovery again and has been automatically relisted!"

    if message.type is discord.MessageType.guild_discovery_grace_period_initial_warning:
        return "This server has failed Discovery activity requirements for 1 week. If this server fails for 4 weeks in a row, it will be automatically removed from Discovery."

    if message.type is discord.MessageType.guild_discovery_grace_period_final_warning:
        return "This server has failed Discovery activity requirements for 3 weeks in a row. If this server fails for 1 more week, it will be removed from Discovery."

    else:
        raise discord.InvalidArgument("This message has an invalid type!")


def bool_friendly_str(bool_to_convert):
    if bool_to_convert == True:
        return "on"
    else:
        return "off"


class CustomCheckFailure(commands.CheckFailure):
    # custom classs for custom prerequisite failures outside of normal command checks
    # this class is so minor i'm not going to bother to migrate it to classes.py
    pass
