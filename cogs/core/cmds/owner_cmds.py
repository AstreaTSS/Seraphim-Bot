#!/usr/bin/env python3.8
import importlib
import typing
from enum import Enum

import discord
from discord.ext import commands

import common.paginator as paginator
import common.star_classes as star_classes
import common.utils as utils


class OwnerCMDs(commands.Cog, name="Owner", command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(
        hidden=True, aliases=["reloadallextensions", "reload_all", "reloadall"]
    )
    async def reload_all_extensions(self, ctx):
        extensions = [i for i in self.bot.extensions.keys() if i != "cogs.db_handler"]
        for extension in extensions:
            await self.bot.reload_extension(extension)

        await ctx.reply("All extensions reloaded!")

    @commands.command(hidden=True)
    async def list_loaded_extensions(self, ctx):
        exten_list = [f"`{k}`" for k in self.bot.extensions.keys()]
        exten_str = ", ".join(exten_list)
        await ctx.reply(f"Extensions: {exten_str}")

    @commands.command(hidden=True, aliases=["list_application_commands", "listappcmds"])
    async def list_app_cmds(
        self, ctx: utils.SeraContextBase, guild: typing.Optional[discord.Guild]
    ):
        async with ctx.typing():
            if not guild:
                app_cmds = await ctx.bot.http.get_global_commands(
                    ctx.bot.application_id
                )
            else:
                app_cmds = await ctx.bot.http.get_guild_commands(
                    ctx.bot.application_id, guild.id
                )

            app_cmd_entries = []

            if not app_cmds:
                raise commands.BadArgument(
                    "This guild/bot does not have any specific application commands."
                )

            for entry in app_cmds:
                entry_str_list = []

                if entry["description"]:
                    entry_str_list.append(entry["description"])
                else:
                    cmd_type = entry.get("type")
                    if not cmd_type or cmd_type == 1:
                        entry_str_list.append("No description provided.")
                    elif cmd_type == 2:
                        entry_str_list.append("A user context menu command.")
                    elif cmd_type == 3:
                        entry_str_list.append("A message context menu command.")

                if options := entry.get("options"):
                    entry_str_list.append("__Arguments:__")

                    for option in options:
                        option_type = discord.AppCommandOptionType(option["type"]).name
                        required_txt = ", required" if option.get("required") else ""
                        entry_str_list.append(
                            f"{option['name']} (type `{option_type}`{required_txt}) -"
                            f" {option['description']}"
                        )

                app_cmd_entries.append(
                    (f"{entry['name']} - ID {entry['id']}", "\n".join(entry_str_list))
                )

        pages = paginator.FieldPages(ctx, entries=app_cmd_entries, per_page=6)
        await pages.paginate()

    @commands.command(hidden=True, aliases=["removeappcmd"])
    async def remove_app_cmd(
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

    @commands.command(hidden=True, aliases=["removeallappcmds"])
    async def remove_all_app_cmds(self, ctx, guild: typing.Optional[discord.Guild]):
        if not guild:
            # this is actually a bulk overwrite, but okay d.py
            await self.bot.http.bulk_upsert_global_commands(self.bot.application_id, [])
        else:
            await self.bot.http.bulk_upsert_guild_commands(
                self.bot.application_id, guild.id, []
            )

        await ctx.reply("Removed all commands.")


async def setup(bot):
    importlib.reload(utils)
    importlib.reload(star_classes)
    importlib.reload(paginator)

    await bot.add_cog(OwnerCMDs(bot))
