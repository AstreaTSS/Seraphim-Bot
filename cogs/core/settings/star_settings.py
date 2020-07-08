from discord.ext import commands
import discord

import common.utils as utils

@commands.group(name="starboard")
@commands.check(utils.proper_permissions)
async def main(ctx):
    """The base for messing around with the starboard. Check the subcommands for more info.
    Requires Manage Server permissions or higher."""
    if ctx.invoked_subcommand == None:
        await ctx.send_help(ctx.command)

@main.command()
@commands.check(utils.proper_permissions)
async def channel(ctx, channel: discord.TextChannel):
    """Sets the starboard channel to the channel mentioned."""
    ctx.bot.config[ctx.guild.id]["starboard_id"] = channel.id
    await ctx.send(f"Set channel to {channel.mention}!")

@main.command()
@commands.check(utils.proper_permissions)
async def limit(ctx, limit: int):
    """Sets the amount of stars needed to get onto the starboard to that number."""
    if limit.isdigit():
        ctx.bot.config[ctx.guild.id]["star_limit"] = int(limit)
        await ctx.send(f"Set limit to {limit}!")
    else:
        await ctx.send("That doesn't seem like a valid number to me...")

@main.command()
@commands.check(utils.proper_permissions)
async def toggle(ctx, toggle: bool):
    """Toggles the entirety of the starboard (including the commands, hopefully) on or off (defaults to off when it joins a new server).
    To toggle it, both the star channel and the star limit must be set beforehand."""

    guild_config = ctx.bot.config[ctx.guild.id]
    if guild_config["starboard_id"] != None and guild_config["star_limit"] != None:
        ctx.bot.config[ctx.guild.id]["star_toggle"] = toggle
        await ctx.send(f"Toggled starboard to {toggle} for this server!")
    else:
        await ctx.send("Either you forgot to set the starboard channel or the star limit. Please try again.")


def star_toggle_check(ctx):
    return ctx.bot.config[ctx.guild.id]["star_toggle"]

@main.group(aliases = ["star_bl", "starblacklist"])
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def blacklist(ctx):
    """The base command for the star blacklist. See the subcommands for more info.
    Requires Manage Server permissions or higher. Running this with no arguments will run the list command."""

    if ctx.invoked_subcommand == None:
        list_cmd = ctx.bot.get_command("settings starboard blacklist list")
        await ctx.invoke(list_cmd)

@blacklist.command(name = "list")
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def _list(ctx):
    """Returns a list of channels that have been blacklisted. Messages from channels that are blacklisted won’t be starred."""

    channel_id_list = ctx.bot.config[ctx.guild.id]["star_blacklist"]
    if channel_id_list != []:
        channel_mentions = []

        for channel_id in channel_id_list:
            channel = await ctx.bot.get_channel(channel_id)

            if channel != None:
                channel_mentions.append(channel.mention)
            else:
                del ctx.bot.config[ctx.guild.id]["star_blacklist"][channel_id]

        if channel_mentions != []:
            await ctx.send(f"Blacklisted channels: {', '.join(channel_mentions)}")
            return
            
    await ctx.send("There's no blacklisted channels for this guild!")

@blacklist.command()
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def add(ctx, channel: discord.TextChannel):
    """Adds the channel to the blacklist."""

    channel_id_list = ctx.bot.config[ctx.guild.id]["star_blacklist"]

    if not channel.id in channel_id_list:
        channel_id_list.append(channel.id)
        ctx.bot.config[ctx.guild.id]["blacklist"] = channel_id_list
        await ctx.send(f"Addded {channel.mention} to the blacklist!")
    else:
        await ctx.send("That channel's already in the blacklist!")

@blacklist.command()
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def remove(ctx, channel: discord.TextChannel):
    """Removes the channel from the blacklist."""

    channel_id_list = ctx.bot.config[ctx.guild.id]["star_blacklist"]

    if channel.id in channel_id_list:
        channel_id_list.remove(channel.id)
        ctx.bot.config[ctx.guild.id]["blacklist"] = channel_id_list
        await ctx.send(f"Removed {channel.mention} from the blacklist!")
    else:
        await ctx.send("That channel's not in the blacklist!")