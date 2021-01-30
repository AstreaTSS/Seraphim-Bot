from discord.ext import commands
import discord, collections, typing

import common.utils as utils
import common.groups as groups
import common.paginator as pagniator

class DefaultValidator(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if argument.lower() != "default":
            raise commands.BadArgument("Input is not 'default'!")
        else:
            return argument.lower()

@groups.group(name="pinboard")
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

    entries_list = collections.deque()
    entries_list.append("Channels mapped:\n")

    for entry in ctx.bot.config[ctx.guild.id]["pin_config"].keys():
        entry_text = None
        try:
            entry_chan = ctx.bot.get_channel(int(entry))
            entry_text = entry_chan.mention
        except ValueError or AttributeError:
            if entry == "default":
                entry_text = entry
            else:
                raise utils.CustomCheckFailure("Something weird happened when trying to run this command, and I couldn't get something. DM Sonic.")

        des_chan = ctx.bot.get_channel(ctx.bot.config[ctx.guild.id]["pin_config"][entry]["destination"])

        if not (entry_text == None or des_chan == None):
            limit = ctx.bot.config[ctx.guild.id]["pin_config"][entry]["limit"]

            entries_list.append(f"{entry_text} -> {des_chan.mention} (Limit: {limit})")
        else:
            del ctx.bot.config[ctx.guild.id]["pin_config"][entry]

    if entries_list != []:
        entries_str = "\n".join(entries_list)
        to_pagniate = pagniator.TextPages(ctx, entries_str, prefix="", suffix="")
        await to_pagniate.paginate()
    else:
        raise utils.CustomCheckFailure("There are no entries for this server!")

@main_cmd.command(name = "map")
@commands.check(utils.proper_permissions)
async def _map(ctx, entry: typing.Union[discord.TextChannel, DefaultValidator], destination: discord.TextChannel, limit: int):
    """Maps overflowing pins from the entry channel (either 'default' or an actual channel) to go to the destination channel. 
    If there are more pins than the limit, it is considered overflowing.
    Requires Manage Server permissions or higher."""

    if isinstance(entry, discord.TextChannel):
        entry_perms = entry.permissions_for(ctx.guild.me)
        entry_check = utils.chan_perm_check(entry, entry_perms)
        if entry_check != "OK":
            raise utils.CustomCheckFailure(entry_check)

    dest_perms = destination.permissions_for(ctx.guild.me)
    dest_check = utils.chan_perm_check(destination, dest_perms)
    if dest_check != "OK":
        raise utils.CustomCheckFailure(dest_check)

    if isinstance(entry, discord.TextChannel):
        ctx.bot.config[ctx.guild.id]["pin_config"][str(entry.id)] = {
            "destination": destination.id,
            "limit": limit
        }
        await ctx.reply(f"Overflowing pins from {entry.mention} will now appear in {destination.mention}.")
    else:
        ctx.bot.config[ctx.guild.id]["pin_config"]["default"] = {
            "destination": destination.id,
            "limit": limit
        }
        await ctx.reply(f"Overflowing pins from channels that are not mapped to any other channels will now appear in {destination.mention}.")

@main_cmd.command(aliases = ["pinlimit"])
@commands.check(utils.proper_permissions)
async def pin_limit(ctx, entry: typing.Union[discord.TextChannel, DefaultValidator], limit: int):
    """Changes the max limit of the entry channel (either 'default' or an actual channel) to the provided limit.
    The channel must have been mapped before.
    Requires Manage Server permissions or higher."""

    try:
        if isinstance(entry, discord.TextChannel):
            ctx.bot.config[ctx.guild.id]["pin_config"][str(entry.id)]["limit"] = limit
            await ctx.reply(f"The pin limit for {entry.mention} is now set to {limit}.")
        else:
            ctx.bot.config[ctx.guild.id]["pin_config"]["default"]["limit"] = limit
            await ctx.reply(f"The pin limit for channels that are not mapped to any other channels is now set to {limit}.")
    except KeyError:
        raise commands.BadArgument("That channel hasn't been mapped before!")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def unmap(ctx, entry: typing.Union[discord.TextChannel, DefaultValidator]):
    """Umaps the entry channel (either 'default' or an actual channel), so overflowing pins do not get put into another channel.
    The channel must have been mapped before.
    Requires Manage Server permissions or higher."""

    try:
        if isinstance(entry, discord.TextChannel):
            del ctx.bot.config[ctx.guild.id]["pin_config"][str(entry.id)]
            await ctx.reply(f"Unmapped {entry.mention}.")
        else:
            del ctx.bot.config[ctx.guild.id]["pin_config"]["default"]
            await ctx.reply(f"Unmapped default pinboard channel.")
    except KeyError:
        raise commands.BadArgument("That channel wasn't mapped in the first place!")