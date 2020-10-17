#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib

import common.utils as utils

class CmdControl(commands.Cog, name="Command Control"):
    def __init__(self, bot):
        self.bot = bot

    class CommandConverter(commands.Converter):
        async def convert(self, ctx, argument):
            command_name = argument.lower().replace("-", "_")
            if command_name == "all":
                return command_name

            command = ctx.bot.get_command(command_name)
            if command == None:
                # one day, i might implement cog disabling, but for not, this is what the bot does
                raise commands.BadArgument("This command does not exist!")

            if command.cog.qualified_name in ("Cog Control", "Eval", "Help"):
                # we don't want these commands to be disabled as they are core parts of the bot
                raise commands.BadArgument("You cannot disable this command!")

            return command.qualified_name

    @commands.check(utils.proper_permissions)
    @commands.command()
    async def disable(self, ctx, member: discord.Member, *, command: CommandConverter):
        """Disables the command specified for the specified user.
        You can disable all commands for a user too by specifing 'all' for a user.
        Can only be used by those who have Manage Server permissions, and cannot be used on yourself."""

        if ctx.author == member:
            raise commands.BadArgument("You cannot blacklist yourself!")
        
        # if the user doesnt already have a disables entry
        if self.bot.config[ctx.guild.id]["disables"]["users"].get(str(member.id)) == None:
            self.bot.config[ctx.guild.id]["disables"]["users"][str(member.id)] = [command]

        # checks if command or 'all' have already been disabled for this user
        elif command in self.bot.config[ctx.guild.id]["disables"]["users"][str(member.id)]:
            raise commands.BadArgument("That user already has that command disabled!")
        elif "all" in self.bot.config[ctx.guild.id]["disables"]["users"][str(member.id)]:
            raise commands.BadArgument("That user already has all commands disabled!")

        else:
            self.bot.config[ctx.guild.id]["disables"]["users"][str(member.id)].append(command)
        
        if command != "all":
            await ctx.send(f"Command `{command}` disabled for {member.display_name}.")
        else:
            await ctx.send(f"All commands disabled for {member.display_name}.")

    @commands.check(utils.proper_permissions)
    @commands.command(aliases=["re_enable"])
    async def reenable(self, ctx, member: discord.Member, *, command: CommandConverter):
        """Re-enables the command specified for the specified user.
        You can re-eanble all commands for a user too (if they were denied all commands) by specifing 'all' for a user.
        Can only be used by those who have Manage Server permissions, and cannot be used on yourself."""

        if ctx.author == member:
            raise commands.BadArgument("You cannot blacklist yourself!")

        if self.bot.config[ctx.guild.id]["disables"]["users"].get(str(member.id)) == None:
            raise commands.BadArgument("This user doesn't have that command disabled!")

        try:
            self.bot.config[ctx.guild.id]["disables"]["users"][str(member.id)].remove(command)
            
            if command != "all":
                await ctx.send(f"Command `{command}` re-enabled for {member.display_name}.")
            else:
                await ctx.send(f"All commands re-enabled for {member.display_name}.")

        except KeyError:
            raise commands.BadArgument("This user doesn't have that command disabled!")

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(CmdControl(bot))