#!/usr/bin/env python3.8
import collections
import logging
import os
import traceback
import typing
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands
from DiscordUtilsMod import InviteTracker


def error_embed_generate(error_msg):
    return discord.Embed(colour=discord.Colour.red(), description=error_msg)


def proper_permissions():
    async def predicate(ctx: commands.Context):
        # checks if author has admin or manage guild perms or is the owner
        permissions = ctx.channel.permissions_for(ctx.author)
        return permissions.administrator or permissions.manage_guild

    return commands.check(predicate)


def bot_proper_perms():
    async def predicate(ctx: commands.Context):
        # checks if the bot has admin or manage guild perms or is the owner
        permissions = ctx.channel.permissions_for(ctx.me)
        if not permissions.administrator:
            raise NotEnoughPerms(
                "The bot does not have the permissions needed to run this command. "
                + "As the bot is in beta right now, it needs administrative"
                " permissions " + "to run its commands."
            )
        return True

    return commands.check(predicate)


async def error_handle(bot, error, ctx: typing.Union[commands.Context, None] = None):
    # handles errors and sends them to owner
    if isinstance(error, aiohttp.ServerDisconnectedError):
        to_send = "Disconnected from server!"
        split = True
    else:
        error_str = error_format(error)
        logging.getLogger("discord").error(error_str)

        error_split = error_str.splitlines()
        chunks = [error_split[x : x + 20] for x in range(0, len(error_split), 20)]
        for chunk_ in chunks:
            chunk_[0] = f"```py\n{chunk_[0]}"
            chunk_[len(chunk_) - 1] += "\n```"

        final_chunks = ["\n".join(chunk) for chunk in chunks]
        if ctx and hasattr(ctx, "message") and hasattr(ctx.message, "jump_url"):
            final_chunks.insert(0, f"Error on: {ctx.message.jump_url}")

        to_send = final_chunks
        split = False

    await msg_to_owner(bot, to_send, split)

    if ctx:
        error_embed = error_embed_generate(
            "An internal error has occured. The bot owner has been notified.\n"
            + f"Error (for bot owner purposes): {error}"
        )

        await ctx.reply(
            embed=error_embed, ephemeral=True,
        )


async def msg_to_owner(bot, content, split=True):
    # sends a message to the owner
    owner = bot.owner
    string = str(content)

    str_chunks = string_split(string) if split else content
    for chunk in str_chunks:
        await owner.send(f"{chunk}")


async def user_from_id(bot, guild, user_id):
    if user_id is None:
        return None

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

    if embed.title and len(embed.title) > 256:
        return False
    if embed.description and len(embed.description) > 4096:
        return False
    if embed.author and embed.author.name and len(embed.author.name) > 256:
        return False
    if embed.footer and embed.footer.text and len(embed.footer.text) > 2048:
        return False
    if embed.fields:
        if len(embed.fields) > 25:
            return False
        for field in embed.fields:
            if field.name and len(field.name) > 1024:
                return False
            if field.value and len(field.value) > 2048:
                return False

    return True


def deny_mentions(user: discord.abc.Snowflake):
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


def error_format(error: Exception):
    # simple function that formats an exception
    return "".join(
        traceback.format_exception(
            etype=type(error), value=error, tb=error.__traceback__
        )
    )


def string_split(string: str):
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


def get_content(message: discord.Message):  # sourcery no-metrics
    """Because system_content isn't perfect.
    More or less a copy of system_content with name being swapped with display_name and DM message types removed."""

    if message.type is discord.MessageType.default:
        return message.content

    if message.type is discord.MessageType.recipient_add:
        if message.channel.type is discord.ChannelType.group:
            return (
                f"{message.author.display_name} added"
                f" {message.mentions[0].display_name} to the group."
            )
        else:
            return (
                f"{message.author.display_name} added"
                f" {message.mentions[0].display_name} to the thread."
            )

    if message.type is discord.MessageType.recipient_remove:
        if message.channel.type is discord.ChannelType.group:
            return (
                f"{message.author.display_name} removed"
                f" {message.mentions[0].display_name} from the group."
            )
        else:
            return (
                f"{message.author.display_name} removed"
                f" {message.mentions[0].display_name} from the thread."
            )

    if message.type is discord.MessageType.channel_name_change:
        return (
            f"{message.author.display_name} changed the channel name:"
            f" **{message.content}**"
        )

    if message.type is discord.MessageType.pins_add:
        return f"{message.author.display_name} pinned a message to this channel."

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

        created_at_ms = int(message.created_at.timestamp() * 1000)
        return formats[created_at_ms % len(formats)].format(message.author.display_name)

    if message.type is discord.MessageType.premium_guild_subscription:
        if not message.content:
            return (
                f"{os.environ.get('BOOST_EMOJI_NAME')} {message.author.display_name} just"
                " boosted the server!"
            )
        else:
            return (
                f"{os.environ.get('BOOST_EMOJI_NAME')} {message.author.display_name} just"
                f" boosted the server **{message.content}** times!"
            )

    if message.type is discord.MessageType.premium_guild_tier_1:
        if not message.content:
            return (
                f"{os.environ.get('BOOST_EMOJI_NAME')} {message.author.display_name} just"
                f" boosted the server! {message.guild} has achieved **Level 1!**"
            )
        else:
            return (
                f"{os.environ.get('BOOST_EMOJI_NAME')} {message.author.display_name} just"
                f" boosted the server **{message.content}** times! {message.guild} has"
                " achieved **Level 1!**"
            )

    if message.type is discord.MessageType.premium_guild_tier_2:
        if not message.content:
            return (
                f"{os.environ.get('BOOST_EMOJI_NAME')} {message.author.display_name} just"
                f" boosted the server! {message.guild} has achieved **Level 2!**"
            )
        else:
            return (
                f"{os.environ.get('BOOST_EMOJI_NAME')} {message.author.display_name} just"
                f" boosted the server **{message.content}** times! {message.guild} has"
                " achieved **Level 2!**"
            )

    if message.type is discord.MessageType.premium_guild_tier_3:
        if not message.content:
            return (
                f"{os.environ.get('BOOST_EMOJI_NAME')} {message.author.display_name} just"
                f" boosted the server! {message.guild} has achieved **Level 3!**"
            )
        else:
            return (
                f"{os.environ.get('BOOST_EMOJI_NAME')} {message.author.display_name} just"
                f" boosted the server **{message.content}** times! {message.guild} has"
                " achieved **Level 3!**"
            )

    if message.type is discord.MessageType.channel_follow_add:
        return (
            f"{message.author.display_name} has added {message.content} to this channel"
        )

    if message.type is discord.MessageType.guild_stream:
        return (
            f"{message.author.display_name} is live! Now streaming"
            f" {message.author.activity.name}"
        )

    if message.type is discord.MessageType.guild_discovery_disqualified:
        return (
            "This server has been removed from Server Discovery because it no longer"
            " passes all the requirements. Check Server Settings for more details."
        )

    if message.type is discord.MessageType.guild_discovery_requalified:
        return (
            "This server is eligible for Server Discovery again and has been"
            " automatically relisted!"
        )

    if message.type is discord.MessageType.guild_discovery_grace_period_initial_warning:
        return (
            "This server has failed Discovery activity requirements for 1 week. If this"
            " server fails for 4 weeks in a row, it will be automatically removed from"
            " Discovery."
        )

    if message.type is discord.MessageType.guild_discovery_grace_period_final_warning:
        return (
            "This server has failed Discovery activity requirements for 3 weeks in a"
            " row. If this server fails for 1 more week, it will be removed from"
            " Discovery."
        )

    if message.type is discord.MessageType.thread_created:
        return (
            f"{message.author.display_name} started a thread: **{message.content}**."
            " See all **threads**."
        )

    if message.type is discord.MessageType.reply:
        return message.content

    if message.type is discord.MessageType.thread_starter_message:
        if message.reference is None or message.reference.resolved is None:
            return "Sorry, we couldn't load the first message in this thread"

        return message.reference.resolved.content  # type: ignore

    if message.type is discord.MessageType.guild_invite_reminder:
        return (
            "Wondering who to invite?\nStart by inviting anyone who can help you build"
            " the server!"
        )

    else:
        raise discord.InvalidArgument("This message has an invalid type!")


def bool_friendly_str(bool_to_convert: bool):
    if bool_to_convert:
        return "on"
    else:
        return "off"


def get_icon_url(asset: discord.Asset, size=128):
    if asset.is_animated():
        return str(asset.replace(format="gif", size=size))
    else:
        return str(asset.replace(format="png", size=size))


def generate_default_embed(
    guild: discord.Guild, title=discord.Embed.Empty, description=discord.Embed.Empty
):
    embed = discord.Embed(
        title=title, colour=discord.Colour(0x4378FC), description=description,
    )
    embed.set_author(
        name=f"{guild.me.name}", icon_url=get_icon_url(guild.me.display_avatar),
    )
    return embed


async def deprecated_cmd(ctx: commands.Context):
    deprecated_embed = discord.Embed(
        colour=discord.Colour.darker_grey(),
        description="This feature is deprecated, "
        + "and will be removed by December 30th."
        + "\nSorry if that's an issue!",
    )

    await ctx.reply(embed=deprecated_embed, delete_after=5)


async def resolve_reply(
    bot: commands.Bot, msg: discord.Message
) -> typing.Optional[discord.Message]:
    reply: typing.Optional[discord.Message] = None

    if msg.reference:
        if (
            msg.reference.resolved
            and isinstance(msg.reference.resolved, discord.Message)
        ) or msg.reference.cached_message:
            # saves time fetching messages if possible
            reply = (
                msg.reference.cached_message  # type: ignore
                or msg.reference.resolved
            )
        elif guild := bot.get_guild(msg.reference.guild_id):  # type: ignore
            chan = guild.get_channel_or_thread(msg.reference.channel_id)  # type: ignore
            try:
                reply = await chan.fetch_message(msg.reference.message_id)  # type: ignore
            except discord.HTTPException or AttributeError:
                pass

    return reply


class CustomCheckFailure(commands.CheckFailure):
    # custom classs for custom prerequisite failures outside of normal command checks
    # this class is so minor i'm not going to bother to migrate it to classes.py
    pass


class NotEnoughPerms(commands.CheckFailure):
    pass


if typing.TYPE_CHECKING:
    # avoids circular imports this way

    import asyncpg
    import common.star_classes as star_classes
    import common.classes as custom_classes
    import common.configs as config

    class SeraphimBase(commands.Bot):
        # this should technically be in custom classes
        # but this is used in a lot of places for typehinting
        config: config.GuildConfigManager
        star_queue: custom_classes.SetNoReaddAsyncQueue
        snipes: typing.Dict[
            typing.Literal["deletes", "edits"],
            typing.Dict[int, typing.List[custom_classes.SnipedMessage]],
        ]
        role_rolebacks: typing.Dict[
            int, typing.Dict[typing.Literal["roles", "time", "id"], typing.Any]
        ]
        image_extensions: typing.Tuple[str, ...]
        added_db_info: bool
        death_messages: typing.Tuple[str, ...]
        pool: asyncpg.Pool
        starboard: star_classes.StarboardEntries
        owner: discord.User
        tracker: InviteTracker

    class SeraContextBase(commands.Context):
        bot: SeraphimBase


else:

    class SeraphimBase(commands.Bot):
        ...

    class SeraContextBase(commands.Context):
        ...
