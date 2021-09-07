import typing

import discord
from discord.ext import commands

import common.classes as cclasses
import common.groups as groups
import common.utils as utils


@groups.group(name="starboard", aliases=["sb"])
@utils.proper_permissions()
@utils.bot_proper_perms()
async def main_cmd(ctx):
    """The base for messing around with the starboard. Check the subcommands for more info.
    Requires Manage Server permissions or higher."""
    if not ctx.invoked_subcommand:
        await ctx.send_help(ctx.command)


@main_cmd.command()
@utils.proper_permissions()
@utils.bot_proper_perms()
async def channel(ctx, channel: typing.Optional[cclasses.ValidChannelConverter]):
    """Allows you to either get the starboard channel (no argument) or set the starboard channel (with argument)."""

    if channel:
        ctx.bot.config.setattr(ctx.guild.id, starboard_id=channel.id)
        await ctx.reply(f"Set channel to {channel.mention}!")
    else:
        starboard_id = ctx.bot.config.getattr(ctx.guild.id, "starboard_id")
        starboard_mention = f"<#{starboard_id}>" if starboard_id else "None"
        await ctx.reply(f"Starboard channel: {starboard_mention}")


@main_cmd.command()
@utils.proper_permissions()
@utils.bot_proper_perms()
async def limit(ctx, limit: typing.Optional[int]):
    """Allows you to either get the amount of stars needed to get on the starboard (no argument) or set the amount (with argument)."""
    if limit:
        if limit <= 0:
            raise commands.BadArgument("The limit needs to be greater than 0!")

        ctx.bot.config.setattr(ctx.guild.id, star_limit=limit)
        await ctx.reply(f"Set limit to {limit}!")
    else:
        await ctx.reply(
            f"Star limit: {ctx.bot.config.getattr(ctx.guild.id, 'star_limit')}"
        )


@main_cmd.command()
@utils.proper_permissions()
@utils.bot_proper_perms()
async def remove_reaction(ctx, toggle: typing.Optional[bool]):
    """Allows you to either see if people who react to a star to their messages will have their reactions removed (no argument) or allows you to toggle that (with argument)."""

    if toggle is None:
        await ctx.reply(
            f"Remove self-reactions: **{utils.bool_friendly_str(ctx.bot.config.getattr(ctx.guild.id, 'remove_reaction'))}**"
        )

    else:
        ctx.bot.config.setattr(ctx.guild.id, remove_reaction=toggle)
        await ctx.reply(
            f"Toggled remove reaction {utils.bool_friendly_str(toggle)} for this server!"
        )


@main_cmd.command()
@utils.proper_permissions()
@utils.bot_proper_perms()
async def toggle(ctx, toggle: typing.Optional[bool]):
    """Allows you to either see if all starboard-related commands and actions are on or off (no argument) or allows you to toggle that (with argument).
    If you wish to set the toggle, both the starboard channel and the star limit must be set first."""

    if toggle is None:
        await ctx.reply(
            f"Starboard: **{utils.bool_friendly_str(ctx.bot.config.getattr(ctx.guild.id, 'star_toggle'))}**"
        )

    else:
        guild_config = ctx.bot.config.get(ctx.guild.id)
        if guild_config.starboard_id and guild_config.star_limit:
            ctx.bot.config.setattr(ctx.guild.id, star_toggle=toggle)
            await ctx.reply(
                f"Turned starboard **{utils.bool_friendly_str(toggle)}** for this server!"
            )
        else:
            raise utils.CustomCheckFailure(
                "Either you forgot to set the starboard channel or the star limit. Please try again."
            )


@main_cmd.command(aliases=["edit_messages, editmessage, editmessages"])
@utils.proper_permissions()
@utils.bot_proper_perms()
async def edit_message(ctx, toggle: typing.Optional[bool]):
    """Controls if the starboard message is edited when the original is. Defaults to being on.
    Displays the current option if no argument is given, sets the current option to the argument (yes/no) if given."""

    if toggle != None:
        ctx.bot.config.setattr(ctx.guild.id, star_edit_messages=toggle)
        await ctx.reply(
            f"Toggled starboard message editing **{utils.bool_friendly_str(toggle)}** for this server!"
        )
    else:
        await ctx.reply(
            f"Starboard message editing: **{utils.bool_friendly_str(ctx.bot.config.getattr(ctx.guild.id, 'star_edit_messages'))}**"
        )


def star_toggle_check(ctx):
    return ctx.bot.config.getattr(ctx.guild.id, "star_toggle")


@main_cmd.group(aliases=["bl"], ignore_extra=True)
@utils.proper_permissions()
@utils.bot_proper_perms()
@commands.check(star_toggle_check)
async def blacklist(ctx):
    """The base command for the star blacklist. See the subcommands for more info.
    Requires Manage Server permissions or higher."""

    if not ctx.invoked_subcommand:
        await ctx.send_help(ctx.command)


@blacklist.command(name="list")
@utils.proper_permissions()
@utils.bot_proper_perms()
@commands.check(star_toggle_check)
async def _list(ctx: commands.Context):
    """Returns a list of channels that have been blacklisted. Messages from channels that are blacklisted won’t be starred."""

    channel_id_list = ctx.bot.config.getattr(ctx.guild.id, "star_blacklist")
    if channel_id_list:
        channel_mentions = []

        for channel_id in channel_id_list.copy():
            channel = ctx.guild.get_channel(channel_id)

            if channel:
                channel_mentions.append(channel.mention)
            else:
                channel_id_list.remove(channel_id)
                ctx.bot.config.setattr(ctx.guild.id, star_blacklist=channel_id_list)

        if channel_mentions:
            await ctx.reply(f"Blacklisted channels: {', '.join(channel_mentions)}")
            return

    raise utils.CustomCheckFailure("There's no blacklisted channels for this guild!")


@blacklist.command()
@utils.proper_permissions()
@utils.bot_proper_perms()
@commands.check(star_toggle_check)
async def add(ctx, channel: cclasses.ValidChannelConverter):
    """Adds the channel to the blacklist."""

    channel_id_list = ctx.bot.config.getattr(ctx.guild.id, "star_blacklist")

    if channel.id not in channel_id_list:
        channel_id_list.append(channel.id)
        ctx.bot.config.setattr(ctx.guild.id, star_blacklist=channel_id_list)
        await ctx.reply(f"Addded {channel.mention} to the blacklist!")
    else:
        raise commands.BadArgument("That channel's already in the blacklist!")


@blacklist.command()
@utils.proper_permissions()
@utils.bot_proper_perms()
@commands.check(star_toggle_check)
async def remove(ctx, channel: discord.TextChannel):
    """Removes the channel from the blacklist."""

    channel_id_list = ctx.bot.config.getattr(ctx.guild.id, "star_blacklist")

    if channel.id in channel_id_list:
        channel_id_list.remove(channel.id)
        ctx.bot.config.setattr(ctx.guild.id, star_blacklist=channel_id_list)
        await ctx.reply(f"Removed {channel.mention} from the blacklist!")
    else:
        raise commands.BadArgument("That channel's not in the blacklist!")
