#!/usr/bin/env python3.8
import importlib
import typing

import discord
from discord.ext import commands

import common.manage_commands as manage_commands
import common.paginator as paginator
import common.star_classes as star_classes
import common.utils as utils


class OwnerCMDs(commands.Cog, name="Owner", command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(hidden=True, aliases=["reloadallextensions"])
    async def reload_all_extensions(self, ctx):
        extensions = [i for i in self.bot.extensions.keys() if i != "cogs.db_handler"]
        for extension in extensions:
            self.bot.reload_extension(extension)

        await ctx.reply("All extensions reloaded!")

    @commands.command(hidden=True)
    async def list_loaded_extensions(self, ctx):
        exten_list = [f"`{k}`" for k in self.bot.extensions.keys()]
        exten_str = ", ".join(exten_list)
        await ctx.reply(f"Extensions: {exten_str}")

    @commands.command(hidden=True, aliases=["list_slash_commands", "listslashcmds"])
    async def list_slash_cmds(self, ctx, guild: typing.Optional[discord.Guild]):
        slash_cmds = await manage_commands.get_all_commands(
            self.bot.user.id, self.bot.http.token, guild.id
        )
        slash_entries = []

        if not slash_cmds:
            raise commands.BadArgument(
                "This guild does not have any specific slash commands."
            )

        for entry in slash_cmds:
            entry_str_list = []

            if "description" in entry.keys():
                entry_str_list.append(entry["description"])
            else:
                entry_str_list.append("No description provided.")

            if "options" in entry.keys():
                entry_str_list.append("__Arguments:__")

                for option in entry["options"]:
                    option_type = option["type"]
                    required_txt = ", required" if option.get("required") else ""
                    entry_str_list.append(
                        f"{option['name']} (type {option_type}{required_txt}) - {option['description']}"
                    )

            slash_entries.append(
                (f"{entry['name']} - ID {entry['id']}", "\n".join(entry_str_list))
            )

        pages = paginator.FieldPages(ctx, entries=slash_entries, per_page=6)
        await pages.paginate()

    @commands.command(hidden=True, aliases=["removeslashcmd"])
    async def remove_slash_cmd(
        self, ctx, cmd: discord.Object, guild: typing.Optional[discord.Guild],
    ):

        await manage_commands.remove_slash_command(
            self.bot.user.id, self.bot.http.token, guild.id, cmd.id
        )
        await ctx.reply("Removed command.")

    @commands.command(hidden=True, aliases=["removeallslashcmds"])
    async def remove_all_slash_cmds(self, ctx, guild: typing.Optional[discord.Guild]):
        await manage_commands.remove_all_commands(
            self.bot.user.id, self.bot.http.token, guild.id
        )
        await ctx.reply("Removed all commands.")


def setup(bot):
    importlib.reload(utils)
    importlib.reload(star_classes)
    importlib.reload(paginator)
    importlib.reload(manage_commands)

    bot.add_cog(OwnerCMDs(bot))
