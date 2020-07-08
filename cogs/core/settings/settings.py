#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib, os, inspect

import common.utils as utils

class Settings(commands.Cog, name="Settings"):
    def __init__(self, bot):
        self.bot = bot
        self.custom_setup()

    @commands.group(invoke_without_command=True, aliases=["config", "conf"])
    @commands.check(utils.proper_permissions)
    async def settings(self, ctx):
        """Base command for managing all settings for the bot."""
        await ctx.send_help(ctx.command)

    def custom_setup(self):
        settings_cmd = self.bot.get_command("settings")
        settings_ext = utils.get_all_extensions(os.environ.get("DIRECTORY_OF_FILE"), "cogs/settings")
        for setting in settings_ext:
            if setting == "cogs.core.settings.settings":
                continue

            spec = importlib.util.find_spec(setting)
            if spec is None:
                raise commands.ExtensionNotFound(setting)

            lib = importlib.util.module_from_spec(spec)
            
            try:
                main = getattr(lib, "main")
            except AttributeError:
                raise commands.NoEntryPointError(setting)

            settings_cmd.add_command(main)

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(Settings(bot))