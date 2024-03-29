import collections
import typing

import discord
from discord.ext import commands

import common.classes as cclasses
import common.groups as groups
import common.paginator as pagniator
import common.utils as utils


class DefaultValidator(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if argument.lower() != "default":
            raise commands.BadArgument("Input is not 'default'!")
        else:
            return argument.lower()


@groups.group(name="pinboard")
@utils.proper_permissions()
@utils.bot_proper_perms()
async def main_cmd(ctx):
    """Base command for managing the pinboard. See the subcommands below.
    Requires Manage Server permissions or higher."""

    if ctx.invoked_subcommand is None:
        await ctx.send_help(ctx.command)


@main_cmd.command(name="list")
@utils.proper_permissions()
@utils.bot_proper_perms()
async def _list(ctx: commands.Context):
    """Returns a list of channels that have their pins mapped to another channel, and the max limit before they overflow to that other channel.
    """

    pin_config = ctx.bot.config.getattr(ctx.guild.id, "pin_config")

    if pin_config == {}:
        raise utils.CustomCheckFailure("There are no entries for this server!")

    entries_list = collections.deque()
    entries_list.append("Channels mapped:\n")

    for entry in pin_config.keys():
        entry_text = None
        try:
            entry_chan = ctx.guild.get_channel(int(entry))
            entry_text = entry_chan.mention
        except ValueError or AttributeError:
            if entry == "default":
                entry_text = entry
            else:
                raise utils.CustomCheckFailure(
                    "Something weird happened when trying to run this command, and I"
                    " couldn't get something. "
                    + "Join the support server to report this."
                )

        des_chan = ctx.guild.get_channel(pin_config[entry]["destination"])

        if entry_text and des_chan:
            limit = pin_config[entry]["limit"]
            reversed = pin_config[entry]["reversed"]

            entries_list.append(
                f"{entry_text} -> {des_chan.mention} (Limit: {limit}, reversed:"
                f" {reversed})"
            )
        else:
            del pin_config[entry]
            ctx.bot.config.setattr(ctx.guild.id, pin_config=pin_config)

    if entries_list != []:
        entries_str = "\n".join(entries_list)
        to_pagniate = pagniator.TextPages(ctx, entries_str, prefix="", suffix="")
        await to_pagniate.paginate()
    else:
        raise utils.CustomCheckFailure("There are no entries for this server!")


@main_cmd.command(name="map")
@utils.proper_permissions()
@utils.bot_proper_perms()
async def _map(
    ctx,
    entry: typing.Union[cclasses.ValidChannelConverter, DefaultValidator],
    destination: cclasses.ValidChannelConverter,
    limit: int,
):
    """Maps overflowing pins from the entry channel (either 'default' or an actual channel) to go to the destination channel.
    If there are more pins than the limit, it is considered overflowing.
    Requires Manage Server permissions or higher."""

    pin_config = ctx.bot.config.getattr(ctx.guild.id, "pin_config")
    if isinstance(entry, discord.TextChannel):
        pin_config[str(entry.id)] = {
            "destination": destination.id,
            "limit": limit,
            "reversed": False,
        }
        await ctx.reply(
            f"Overflowing pins from {entry.mention} will now appear in"
            f" {destination.mention}."
        )
    else:
        pin_config["default"] = {
            "destination": destination.id,
            "limit": limit,
            "reversed": False,
        }
        await ctx.reply(
            "Overflowing pins from channels that are not mapped to any other channels"
            f" will now appear in {destination.mention}."
        )
    ctx.bot.config.setattr(ctx.guild.id, pin_config=pin_config)


@main_cmd.command(aliases=["pinlimit"])
@utils.proper_permissions()
@utils.bot_proper_perms()
async def pin_limit(
    ctx, entry: typing.Union[discord.TextChannel, DefaultValidator], limit: int
):
    """Changes the max limit of the entry channel (either 'default' or an actual channel) to the provided limit.
    The channel must have been mapped before.
    Requires Manage Server permissions or higher."""

    try:
        pin_config = ctx.bot.config.getattr(ctx.guild.id, "pin_config")
        if isinstance(entry, discord.TextChannel):
            pin_config[str(entry.id)]["limit"] = limit
            await ctx.reply(f"The pin limit for {entry.mention} is now set to {limit}.")
        else:
            pin_config["default"]["limit"] = limit
            await ctx.reply(
                "The pin limit for channels that are not mapped to any other channels"
                f" is now set to {limit}."
            )
        ctx.bot.config.setattr(ctx.guild.id, pin_config=pin_config)
    except KeyError:
        raise commands.BadArgument("That channel hasn't been mapped before!")


@main_cmd.command()
@utils.proper_permissions()
@utils.bot_proper_perms()
async def unmap(ctx, entry: typing.Union[discord.TextChannel, DefaultValidator]):
    """Umaps the entry channel (either 'default' or an actual channel), so overflowing pins do not get put into another channel.
    The channel must have been mapped before.
    Requires Manage Server permissions or higher."""

    try:
        pin_config = ctx.bot.config.getattr(ctx.guild.id, "pin_config")
        if isinstance(entry, discord.TextChannel):
            del pin_config[str(entry.id)]
            await ctx.reply(f"Unmapped {entry.mention}.")
        else:
            del pin_config["default"]
            await ctx.reply(f"Unmapped default pinboard channel.")
        ctx.bot.config.setattr(ctx.guild.id, pin_config=pin_config)
    except KeyError:
        raise commands.BadArgument("That channel wasn't mapped in the first place!")


@main_cmd.command(aliases=["reversed"])
@utils.proper_permissions()
@utils.bot_proper_perms()
async def reverse(
    ctx, entry: typing.Union[discord.TextChannel, DefaultValidator], value: bool
):
    """Determines if the way old pins are removed are reversed or not.
    Typically, if an overflowing pin is added, the oldest pin entry gets removed to make way for the new pin.
    This effectively makes it so the new pin gets sent to the pinboard instead.
    Useful if you wish to keep a few pins around forever."""

    try:
        pin_config = ctx.bot.config.getattr(ctx.guild.id, "pin_config")
        if isinstance(entry, discord.TextChannel):
            pin_config[str(entry.id)]["reversed"] = value
            await ctx.reply(
                f"Set if the pin removal is reversed or not for {entry.mention} to:"
                f" {value}."
            )
        else:
            pin_config["default"]["reversed"] = value
            await ctx.reply(
                "Set if the pin removal is reversed or not for the "
                + f"default pinboard channel to: {value}."
            )
        ctx.bot.config.setattr(ctx.guild.id, pin_config=pin_config)
    except KeyError:
        raise commands.BadArgument("That channel wasn't mapped in the first place!")
