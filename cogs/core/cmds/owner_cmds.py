#!/usr/bin/env python3.8
import importlib
import typing
from enum import Enum

import discord
from discord.ext import commands
from discord.types.interactions import ApplicationCommandOption

import common.paginator as paginator
import common.star_classes as star_classes
import common.utils as utils


class OwnerCMDs(commands.Cog, name="Owner", command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

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

    class OptionTypeEnum(Enum):
        SUB_COMMAND = 1
        SUB_COMMAND_GROUP = 2
        STRING = 3
        INTEGER = 4
        BOOLEAN = 5
        USER = 6
        CHANNEL = 7
        ROLE = 8
        MENTIONABLE = 9
        NUMBER = 10

    @commands.command(hidden=True, aliases=["list_slash_commands", "listslashcmds"])
    async def list_slash_cmds(
        self, ctx: utils.SeraContextBase, guild: typing.Optional[discord.Guild]
    ):

        if not guild:
            app_cmds = await ctx.bot.http.get_global_commands(ctx.bot.application_id)
        else:
            app_cmds = await ctx.bot.http.get_guild_commands(
                ctx.bot.application_id, guild.id
            )

        slash_entries = []

        if not app_cmds:
            raise commands.BadArgument(
                "This guild/bot does not have any specific slash commands."
            )

        for entry in app_cmds:
            if entry.get("type", 0) == 1:
                entry_str_list = []

                if entry["description"]:
                    entry_str_list.append(entry["description"])
                else:
                    entry_str_list.append("No description provided.")

                if entry.get("options"):
                    entry_str_list.append("__Arguments:__")

                    for option in entry["options"]:  # type: ignore
                        option: ApplicationCommandOption
                        option_type = self.OptionTypeEnum(option["type"]).name
                        required_txt = ", required" if option["required"] else ""
                        entry_str_list.append(
                            f"{option['name']} (type {option_type}{required_txt}) - {option['description']}"
                        )

                slash_entries.append(
                    (f"{entry['name']} - ID {entry['id']}", "\n".join(entry_str_list))
                )

        if not slash_entries:
            raise commands.BadArgument(
                "This guild/bot does not have any specific slash commands."
            )

        pages = paginator.FieldPages(ctx, entries=slash_entries, per_page=6)
        await pages.paginate()

    @commands.command(hidden=True, aliases=["removeslashcmd"])
    async def remove_slash_cmd(
        self,
        ctx,
        cmd: discord.Object,
        guild: typing.Optional[discord.Guild],
    ):
        if guild:
            await self.bot.http.delete_guild_command(
                self.bot.application_id, guild.id, cmd.id
            )
        else:
            await self.bot.http.delete_global_command(self.bot.application_id, cmd.id)

        await ctx.reply("Removed command.")

    @commands.command(hidden=True, aliases=["removeallslashcmds"])
    async def remove_all_slash_cmds(self, ctx, guild: typing.Optional[discord.Guild]):
        if not guild:
            app_cmds = await self.bot.http.get_global_commands(self.bot.application_id)
        else:
            app_cmds = await self.bot.http.get_guild_commands(
                self.bot.application_id, guild.id
            )

        slash_cmd_ids = [e["id"] for e in app_cmds if e.get("type", 0) == 1]

        for cmd_id in slash_cmd_ids:
            if not guild:
                await self.bot.http.delete_global_command(
                    self.bot.application_id, cmd_id
                )
            else:
                await self.bot.http.delete_guild_command(
                    self.bot.application_id, guild.id, cmd_id
                )

        await ctx.reply("Removed all commands.")


def setup(bot):
    importlib.reload(utils)
    importlib.reload(star_classes)
    importlib.reload(paginator)

    bot.add_cog(OwnerCMDs(bot))
