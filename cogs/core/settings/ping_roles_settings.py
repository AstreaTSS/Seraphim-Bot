import discord
from discord.ext import commands

import common.classes
import common.fuzzys as fuzzys
import common.groups as groups
import common.utils as utils


@groups.group(
    name="ping_roles", aliases=["pingroles", "pingrole", "rolepings", "roleping"]
)
@commands.check(utils.proper_permissions)
async def main_cmd(ctx):
    """The base command for managing all of the pingable roles. See the help for the subcommands for more info.
    Only people with Manage Server permissions or higher can use these commands."""

    if ctx.invoked_subcommand is None:
        await ctx.send_help(ctx.command)


@main_cmd.command()
async def list(ctx: commands.Context):
    """Lists the pingable roles. It does the same as the pingroles command."""
    ping_roles_cmd = ctx.bot.get_command("ping_roles")
    await ping_roles_cmd.invoke(ctx)


@main_cmd.command()
@commands.check(utils.proper_permissions)
async def add(
    ctx,
    role: fuzzys.FuzzyRoleConverter,
    *,
    cooldown: common.classes.TimeDurationConverter,
):
    """Adds the role to the roles able to be pinged.
    The role can be an ID, a mention, or a name. If it's a name and the name is more than one word, that it must be in quotes.
    The cooldown can be in seconds, minutes, hours, days, months, and/or years (ex. 1s, 1m, 1h 20.5m)."""

    top_role = ctx.guild.me.top_role

    if role > top_role:
        raise utils.CustomCheckFailure(
            "The role provided is a role that is higher than the roles I can edit. Please move either that role or my role so that "
            + "my role is higher than the role you want to be pingable."
        )

    pingable_roles = ctx.bot.config.getattr(ctx.guild.id, "pingable_roles")

    if str(role.id) in pingable_roles:
        raise utils.CustomCheckFailure("That role is already pingable!")

    period = cooldown.total_seconds()

    pingable_roles[str(role.id)] = {"time_period": period, "last_used": 0}
    ctx.bot.config.setattr(ctx.guild.id, pingable_roles=pingable_roles)

    await ctx.reply("Role added!")


@main_cmd.command()
@commands.check(utils.proper_permissions)
async def cooldown(
    ctx,
    role: fuzzys.FuzzyRoleConverter,
    *,
    cooldown: common.classes.TimeDurationConverter,
):
    """Changes the cooldown of the role.
    The role can be an ID, a mention, or a name. If it's a name and the name is more than one word, that it must be in quotes.
    The cooldown can be in seconds, minutes, hours, days, months, and/or years (ex. 1s, 1m, 1h 20.5m)."""

    pingable_roles = ctx.bot.config.getattr(ctx.guild.id, "pingable_roles")

    if str(role.id) not in pingable_roles:
        raise commands.BadArgument("That's not a pingable role!")

    period = cooldown.total_seconds()

    pingable_roles[str(role.id)]["time_period"] = period
    ctx.bot.config.setattr(ctx.guild.id, pingable_roles=pingable_roles)

    await ctx.reply("Role cooldown changed!")


@main_cmd.command()
@commands.check(utils.proper_permissions)
async def remove(ctx, *, role: fuzzys.FuzzyRoleConverter):
    """Removes that role from the roles able to be pinged.
    The role can be an ID, a mention, or a name. If it's a name, it does not need to be in quotes."""

    ping_roles = ctx.bot.config.getattr(ctx.guild.id, "pingable_roles")

    if ping_roles == {}:
        raise utils.CustomCheckFailure("There are no pingable roles to remove!")

    if str(role.id) not in ping_roles.keys():
        raise commands.BadArgument("That role isn't on the ping list!")

    del ping_roles[str(role.id)]
    ctx.bot.config.setattr(ctx.guild.id, pingable_roles=ping_roles)

    await ctx.reply(
        f"Deleted {role.mention}!",
        allowed_mentions=discord.AllowedMentions(roles=False),
    )
