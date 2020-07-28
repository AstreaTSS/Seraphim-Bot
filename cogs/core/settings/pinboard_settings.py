from discord.ext import commands
import discord

import common.utils as utils

@commands.group(name="pinboard")
@commands.check(utils.proper_permissions)
async def main_cmd(ctx):
    """Base command for managing the pinboard. See the subcommands below. 
    Requires Manage Server permissions or higher."""

    if ctx.invoked_subcommand == None:
        await ctx.send_help(ctx.command)

@main_cmd.command(name = "list")
@commands.check(utils.proper_permissions)
async def _list(ctx):
    """Returns a list of channels that have their pins mapped to another channel, and the max limit before they overflow to that other channel."""

    if ctx.bot.config[ctx.guild.id]["pin_config"] == {}:
        raise utils.CustomCheckFailure("There are no entries for this server!")

    entries_list = []

    for entry in ctx.bot.config[ctx.guild.id]["pin_config"].keys():
        entry_chan = ctx.bot.get_channel(int(entry))
        des_chan = ctx.bot.get_channel(ctx.bot.config[ctx.guild.id]["pin_config"][entry]["destination"])

        if not (entry_chan == None or des_chan == None):
            limit = ctx.bot.config[ctx.guild.id]["pin_config"][entry]["limit"]

            entries_list.append(f"{entry_chan.mention} -> {des_chan.mention} (Limit: {limit})")
        else:
            del ctx.bot.config[ctx.guild.id]["pin_config"][entry]

    if entries_list != []:
        entries_str = "\n".join(entries_list)
        await ctx.send(f"Channels mapped:\n\n{entries_str}")
    else:
        raise utils.CustomCheckFailure("There are no entries for this server!")

@main_cmd.command(name = "map")
@commands.check(utils.proper_permissions)
async def _map(ctx, entry: discord.TextChannel, destination: discord.TextChannel, limit: int):
    """Maps overflowing pins from the entry channel to go to the destination channel. 
    If there are more pins than the limit, it is considered overflowing."""

    entry_perms = entry.permissions_for(ctx.guild.me)
    entry_check = utils.chan_perm_check(entry, entry_perms)
    if entry_check != "OK":
        raise utils.CustomCheckFailure(entry_check)

    dest_perms = destination.permissions_for(ctx.guild.me)
    dest_check = utils.chan_perm_check(destination, dest_perms)
    if dest_check != "OK":
        raise utils.CustomCheckFailure(entry_check)

    ctx.bot.config[ctx.guild.id]["pin_config"][str(entry.id)] = {
        "destination": destination.id,
        "limit": limit
    }

    await ctx.send(f"Overflowing pins from {entry.mention} will now appear in {destination.mention}.")

@main_cmd.command(aliases = ["pinlimit"])
@commands.check(utils.proper_permissions)
async def pin_limit(ctx, entry: discord.TextChannel, limit: int):
    """Changes the max limit of the entry channel to the provided limit."""

    ctx.bot.config[ctx.guild.id]["pin_config"][str(entry.id)]["limit"] = limit
    await ctx.send(f"The pin limit for {entry.mention} is now set to {limit}.")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def unmap(ctx, entry: discord.TextChannel):
    """Umaps the entry channel, so overflowing pins do not get put into another channel."""

    try:
        del ctx.bot.config[ctx.guild.id]["pin_config"][str(entry.id)]
        await ctx.send(f"Unmapped {entry.mention}.")
    except KeyError:
        raise commands.BadArgument("That channel wasn't mapped in the first place!")