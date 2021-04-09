from discord.ext import commands
import discord, typing

import common.utils as utils
import common.groups as groups

class BoolConverter(commands.Converter):
    """Because Discord is weird."""
    async def convert(self, ctx, argument):
        lowered = argument.lower()

        if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            return True
        elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            return False
        else:
            raise commands.BadBoolArgument


@groups.group(name="starboard", aliases=["sb"])
@commands.check(utils.proper_permissions)
async def main_cmd(ctx):
    """The base for messing around with the starboard. Check the subcommands for more info.
    Requires Manage Server permissions or higher."""
    if not ctx.invoked_subcommand:
        await ctx.send_help(ctx.command)

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def channel(ctx, channel: typing.Optional[discord.TextChannel]):
    """Allows you to either get the starboard channel (no argument) or set the starboard channel (with argument)."""

    if channel:
        ctx.bot.config.setattr(ctx.guild.id, starboard_id=channel.id)
        await ctx.reply(f"Set channel to {channel.mention}!")
    else:
        starboard_id = ctx.bot.config.getattr(ctx.guild.id, 'starboard_id')
        starboard_mention = f"<#{starboard_id}>" if starboard_id else "None"
        await ctx.reply(f"Starboard channel: {starboard_mention}")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def limit(ctx, limit: typing.Optional[int]):
    """Allows you to either get the amount of stars needed to get on the starboard (no argument) or set the amount (with argument)."""
    if limit:
        if limit > 0:
            ctx.bot.config.setattr(ctx.guild.id, star_limit=limit)
            await ctx.reply(f"Set limit to {limit}!")
        else:
            raise commands.BadArgument("The limit needs to be greater than 0!")
    else:
        await ctx.reply(f"Star limit: {ctx.bot.config.getattr(ctx.guild.id, 'star_limit')}")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def remove_reaction(ctx, toggle: typing.Optional[BoolConverter]):
    """Allows you to either see if people who react to a star to their messages will have their reactions removed (no argument) or allows you to toggle that (with argument)."""
    if toggle:
        ctx.bot.config.setattr(ctx.guild.id, remove_reaction=toggle)
        await ctx.reply(f"Toggled remove reaction to {toggle} for this server!")
    else:
        await ctx.reply(f"Remove reaction: {ctx.bot.config.getattr(ctx.guild.id, 'remove_reaction')}")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def toggle(ctx, toggle: typing.Optional[BoolConverter]):
    """Allows you to either see if all starboard-related commands and actions are on or off (no argument) or allows you to toggle that (with argument).
    If you wish to set the toggle, both the starboard channel and the star limit must be set first."""

    if toggle:
        guild_config = ctx.bot.config.get(ctx.guild.id)
        if guild_config.starboard_id and guild_config.star_limit:
            ctx.bot.config.setattr(ctx.guild.id, star_toggle=toggle)
            await ctx.reply(f"Toggled starboard to {toggle} for this server!")
        else:
            raise utils.CustomCheckFailure("Either you forgot to set the starboard channel or the star limit. Please try again.")
    else:
        await ctx.reply(f"Star toggle: {ctx.bot.config.getattr(ctx.guild.id, 'star_toggle')}")

@main_cmd.command(aliases=["edit_messages, editmessage, editmessages"])
@commands.check(utils.proper_permissions)
async def edit_message(ctx, toggle: typing.Optional[BoolConverter]):
    """Controls if the starboard message is edited when the original is. Defaults to being on.
    Displays the current option if no argument is given, sets the current option to the argument (yes/no) if given."""

    if toggle:
        ctx.bot.config.setattr(ctx.guild.id, star_edit_messages=toggle)
        await ctx.reply(f"Toggled starboard message editing to {toggle} for this server!")
    else:
        await ctx.reply(f"Star toggle: {ctx.bot.config.getattr(ctx.guild.id, 'star_edit_messages')}")


def star_toggle_check(ctx):
    return ctx.bot.config.getattr(ctx.guild.id, 'star_toggle')

@main_cmd.group(aliases = ["bl"], ignore_extra=True)
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def blacklist(ctx):
    """The base command for the star blacklist. See the subcommands for more info.
    Requires Manage Server permissions or higher."""

    if not ctx.invoked_subcommand:
        await ctx.send_help(ctx.command)

@blacklist.command(name = "list")
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def _list(ctx):
    """Returns a list of channels that have been blacklisted. Messages from channels that are blacklisted won’t be starred."""

    channel_id_list = ctx.bot.config.getattr(ctx.guild.id, "star_blacklist")
    if channel_id_list:
        channel_mentions = []

        for channel_id in channel_id_list.copy():
            channel = ctx.bot.get_channel(channel_id)

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
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def add(ctx, channel: discord.TextChannel):
    """Adds the channel to the blacklist."""

    chan_perms = channel.permissions_for(ctx.guild.me)
    chan_check = utils.chan_perm_check(channel, chan_perms)
    if chan_check != "OK":
        raise utils.CustomCheckFailure(chan_check)

    channel_id_list = ctx.bot.config.getattr(ctx.guild.id, "star_blacklist")

    if not channel.id in channel_id_list:
        channel_id_list.append(channel.id)
        ctx.bot.config.setattr(ctx.guild.id, star_blacklist=channel_id_list)
        await ctx.reply(f"Addded {channel.mention} to the blacklist!")
    else:
        raise commands.BadArgument("That channel's already in the blacklist!")

@blacklist.command()
@commands.check(utils.proper_permissions)
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