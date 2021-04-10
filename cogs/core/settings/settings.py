#!/usr/bin/env python3.8
import importlib
import os

from discord.ext import commands

import common.groups as groups
import common.utils as utils


class Settings(commands.Cog, name="Settings"):
    def __init__(self, bot):
        self.bot = bot
        self.custom_setup()

    @groups.group(invoke_without_command=True, aliases=["config", "conf"])
    @commands.check(utils.proper_permissions)
    async def settings(self, ctx):
        """Base command for managing all settings for the bot. This is where you set up the starboard, pinboard, and pingable roles."""
        await ctx.send_help(ctx.command)

    def custom_setup(self):
        settings_cmd = None

        for cmd in self.get_commands():
            if cmd.name == "settings":
                settings_cmd = cmd

        if settings_cmd == None:
            raise commands.CommandNotFound("Can't find settings command!")

        settings_ext = utils.get_all_extensions(
            os.environ.get("DIRECTORY_OF_FILE"), "cogs/core/settings"
        )
        for setting in settings_ext:
            if setting == "cogs.core.settings.settings":
                continue

            lib = importlib.import_module(setting)
            importlib.reload(lib)
            main = getattr(lib, "main_cmd")

            settings_cmd.add_command(main)

    def cog_unload(self):
        settings_cmd = None

        for cmd in self.get_commands():
            if cmd.name == "settings":
                settings_cmd = cmd

        if settings_cmd == None:
            raise commands.CommandNotFound("Can't find settings command!")

        for cmd in settings_cmd.copy().walk_commands():
            self.bot.remove_command(cmd.qualified_name)

        self.bot.remove_command(settings_cmd.name)


def setup(bot):
    importlib.reload(utils)
    importlib.reload(groups)
    bot.add_cog(Settings(bot))
