from discord.ext import commands
import discord, datetime, humanize

import common.utils as utils

@commands.group(name="ping_roles")
@commands.check(utils.proper_permissions)
async def main_cmd(ctx):
    """The base command for managing all of the pingable roles. See the help for the subcommands for more info.
    Only people with Manage Server permissions or higher can use these commands."""
    
    if ctx.invoked_subcommand == None:
        await ctx.send_help(ctx.command)

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def add(ctx, role: discord.Role, *, cooldown: utils.TimeDurationConverter):
    """Adds the role to the roles able to be pinged. 
    The role can be an ID, a mention, or a name. If it's a name, it's case sensitive and, if the name is more than one word, that it must be in quotes.
    The cooldown can be in seconds, minutes, hours, days, months, and/or years (ex. 1s, 1m, 1h 20.5m)."""

    top_role = ctx.guild.me.top_role

    if role > top_role:
        raise utils.CustomCheckFailure(
            "The role provided is a role that is higher than the roles I can edit. Please move either that role or my role so that " +
            "my role is higher than the role you want to be pingable."
        )

    if str(role.id) in ctx.bot.config[ctx.guild.id]["pingable_roles"]:
        raise utils.CustomCheckFailure("That role is already pingable!")

    period = cooldown.total_seconds()

    ctx.bot.config[ctx.guild.id]["pingable_roles"][str(role.id)] = {
        "time_period": period,
        "last_used": 0
    }

    await ctx.send("Role added!")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def cooldown(ctx, role: discord.Role, *, cooldown: utils.TimeDurationConverter):
    """Changes the cooldown of the role. 
    The role can be an ID, a mention, or a name. If it's a name, it's case sensitive and, if the name is more than one word, that it must be in quotes.
    The cooldown can be in seconds, minutes, hours, days, months, and/or years (ex. 1s, 1m, 1h 20.5m)."""

    if not str(role.id) in ctx.bot.config[ctx.guild.id]["pingable_roles"]:
        raise commands.BadArgument("That's not a pingable role!")

    period = cooldown.total_seconds()

    ctx.bot.config[ctx.guild.id]["pingable_roles"][str(role.id)]["time_period"] = period

    await ctx.send("Role cooldown changed!")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def remove(ctx, *, role: discord.Role):
    """Removes that role from the roles able to be pinged. 
    The role can be an ID, a mention, or a name. If it's a name, it's case sensitive, however, it does not need to be in quotes."""

    ping_roles = ctx.bot.config[ctx.guild.id]["pingable_roles"]

    if ping_roles == {}:
        raise utils.CustomCheckFailure("There are no pingable roles to remove!")

    if not str(role.id) in ping_roles.keys():
        raise commands.BadArgument("That role isn't on the ping list!")

    del ctx.bot.config[ctx.guild.id]["pingable_roles"][str(role.id)]

    await ctx.send(f"Deleted {role.mention}!", allowed_mentions=discord.AllowedMentions(roles=False))