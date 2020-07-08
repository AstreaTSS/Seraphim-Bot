from discord.ext import commands
import discord, datetime, humanize

import common.utils as utils

@commands.group(name="ping_roles")
@commands.check(utils.proper_permissions)
async def main_cmd(ctx):
    """The base command for managing all of the pingable roles. See the help for the subcommands for more info.
    Only people with Manage Server permissions or higher can use this."""
    
    if ctx.invoked_subcommand == None:
        await ctx.send_help(ctx.command)

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def add(ctx, role_name, *, cooldown: utils.TimeDurationConverter):
    """Adds the role to the roles able to be pinged. 
    The role name is case-sensitive, and must be in quotes if it’s over one word. 
    The cooldown can be in seconds, minutes, hours, days, months, and/or years (ex. 1s, 1m, 1h 20.5m)."""

    role_obj = discord.utils.get(ctx.guild.roles, name = role_name)
    if role_obj == None:
        await ctx.send("That's not a role! Make sure it's spelled correctly, and if it has multiple words, that it's in quotes.")
        return

    if str(role_obj.id) in ctx.bot.config[ctx.guild.id]["pingable_roles"]:
        await ctx.send("That role is already pingable! If you wish to change the cooldown, for now, remove and re-add the role.")
        return

    period = cooldown.total_seconds()

    ctx.bot.config[ctx.guild.id]["pingable_roles"][str(role_obj.id)] = {
        "time_period": period,
        "last_used": 0
    }

    await ctx.send("Role added!")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def cooldown(ctx, role_name, *, cooldown: utils.TimeDurationConverter):
    """Changes the cooldown of the role. 
    The role name is case-sensitive, and must be in quotes if it’s over one word. 
    The cooldown can be in seconds, minutes, hours, days, months, and/or years (ex. 1s, 1m, 1h 20.5m)."""

    role_obj = discord.utils.get(ctx.guild.roles, name = role_name)
    if role_obj == None:
        await ctx.send("That's not a role! Make sure it's spelled correctly, and if it has multiple words, that it's in quotes.")
        return

    if not str(role_obj.id) in ctx.bot.config[ctx.guild.id]["pingable_roles"]:
        await ctx.send("That role isn't on the ping list!")
        return

    period = cooldown.total_seconds()

    ctx.bot.config[ctx.guild.id]["pingable_roles"][str(role_obj.id)]["time_period"] = period

    await ctx.send("Role cooldown changed!")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def remove(ctx, *, role_name):
    """Removes that role from the roles able to be pinged. 
    Role name is case-sensitive, although it does not need to be in quotes if it’s over one word. 
    This is the only way to ‘edit’ a role’s cooldown; removing it and adding it back in with the new cooldown."""

    ping_roles = ctx.bot.config[ctx.guild.id]["pingable_roles"]

    if ping_roles == {}:
        await ctx.send("There are no roles added for you to remove!")
        return

    role_obj = discord.utils.get(ctx.guild.roles, name = role_name)

    if role_obj == None:
        await ctx.send("That role doesn't exist!")
        return
    if not str(role_obj.id) in ping_roles.keys():
        await ctx.send("That role isn't on the ping list!")
        return

    del ctx.bot.config[ctx.guild.id]["pingable_roles"][str(role_obj.id)]

    await ctx.send("Deleted!")