#!/usr/bin/env python3.8
import asyncio
import importlib
import typing

from discord.ext import commands
from discord.ext import tasks

import common.star_classes as star_classes
import common.utils as utils


class DBHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.commit_loop.start()

    def cog_unload(self):
        self.commit_loop.cancel()

    async def get_dbs(self):
        starboard_db = await self.fetch_table("starboard")
        config_db = await self.fetch_table("seraphim_config")

        for row in starboard_db:
            entry = star_classes.StarboardEntry.from_row(row)
            self.bot.starboard.add(entry, init=True)

        for row in config_db:
            self.bot.config.import_entry(row)

        self.bot.added_db_info = True

    def get_required_from_entry(self, entry: star_classes.StarboardEntry):
        return (
            entry.ori_mes_id,
            entry.ori_chan_id,
            entry.star_var_id,
            entry.starboard_id,
            entry.author_id,
            list(entry.ori_reactors),
            list(entry.var_reactors),
            entry.guild_id,
            entry.forced,
            entry.frozen,
            entry.trashed,
        )

    @tasks.loop(minutes=2)
    async def commit_loop(self):
        insert_sb = []
        update_sb = []

        for entry_id in self.bot.starboard.added:
            entry = self.bot.starboard.get(entry_id)
            insert_sb.append(self.get_required_from_entry(entry))
        for entry_id in self.bot.starboard.updated:
            entry = self.bot.starboard.get(entry_id)
            update_sb.append(self.get_required_from_entry(entry))
        delete_sb = tuple(tuple(entry_id) for entry_id in self.bot.starboard.removed)
        self.bot.starboard.reset_deltas()

        insert_config = [
            (guild_id, self.bot.config.get(guild_id).to_dict())
            for guild_id in self.bot.config.added
        ]
        update_config = [
            (guild_id, self.bot.config.get(guild_id).to_dict())
            for guild_id in self.bot.config.updated
        ]
        self.bot.config.reset_deltas()

        if insert_config or update_config or delete_sb or insert_sb or update_sb:
            await self.update_db(
                insert_config, update_config, delete_sb, insert_sb, update_sb
            )

    @commit_loop.error
    async def error_handle(self, *args):
        error = args[-1]
        await utils.error_handle(self.bot, error)

    @commit_loop.before_loop
    async def before_commit_loop(self):
        if self.bot.init_load:
            await self.get_dbs()

            while self.bot.config.entries == {}:
                await asyncio.sleep(0.1)

        await asyncio.sleep(60)

    async def fetch_table(self, table):
        async with self.bot.pool.acquire() as conn:
            data = await conn.fetch(f"SELECT * FROM {table}")

        return data

    async def update_db(
        self,
        insert_config: typing.Tuple[int, dict],
        update_config: typing.Tuple[int, dict],
        delete_sb: typing.Tuple[typing.Tuple[int]],
        insert_sb: typing.Tuple[int, star_classes.StarboardEntry],
        update_sb: typing.Tuple[int, star_classes.StarboardEntry],
    ):
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                if insert_config:
                    await conn.executemany(
                        "INSERT INTO seraphim_config(guild_id, config) VALUES($1, $2)",
                        args=insert_config,
                    )
                if update_config:
                    await conn.executemany(
                        "UPDATE seraphim_config SET config = $2 WHERE guild_id = $1",
                        args=update_config,
                    )

                if delete_sb:
                    await conn.executemany(
                        "DELETE FROM starboard WHERE ori_mes_id = $1", args=delete_sb
                    )
                if insert_sb:
                    str_builder = [
                        "INSERT INTO starboard(ori_mes_id, ori_chan_id, star_var_id, ",
                        "starboard_id, author_id, ori_reactors, var_reactions ",
                        "guild_id, forced, frozen, trashed) VALUES($1, $2, $3, $4, ",
                        "$5, $6, $7, $8, $9, $10, $11)",
                    ]
                    query = "".join(str_builder)
                    await conn.executemany(query, args=insert_sb)
                if update_sb:
                    str_builder = [
                        "UPDATE starboard SET ori_chan_id = $2, star_var_id = $3, starboard_id = $4, ",
                        "author_id = $5, ori_reactors = $6, var_reactions = $7, guild_id = $8, ",
                        "forced = $9, frozen = $10, trashed = $11 WHERE ori_mes_id = $1",
                    ]
                    query = "".join(str_builder)
                    await conn.executemany(query, args=update_sb)


def setup(bot):
    importlib.reload(utils)
    bot.add_cog(DBHandler(bot))
