#!/usr/bin/env python3.8
import asyncio
import importlib
import typing

from discord.ext import commands
from discord.ext import tasks

import common.utils as utils


class DBHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: utils.SeraphimBase = bot
        self.commit_loop.start()

    def cog_unload(self):
        self.commit_loop.cancel()

    async def get_dbs(self):
        config_db = await self.fetch_table("seraphim_config")

        for row in config_db:
            self.bot.config.import_entry(row)

        self.bot.added_db_info = True

    @tasks.loop(minutes=2)
    async def commit_loop(self):
        insert_config = [
            (guild_id, self.bot.config.get(guild_id).to_dict())
            for guild_id in self.bot.config.added
        ]
        update_config = [
            (guild_id, self.bot.config.get(guild_id).to_dict())
            for guild_id in self.bot.config.updated
        ]
        self.bot.config.reset_deltas()

        if insert_config or update_config:
            await self.update_db(insert_config, update_config)

    @commit_loop.error
    async def error_handle(self, *args):
        error = args[-1]
        await utils.error_handle(self.bot, error)

    @commit_loop.before_loop
    async def before_commit_loop(self):
        if not self.bot.added_db_info:
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


def setup(bot):
    importlib.reload(utils)
    bot.add_cog(DBHandler(bot))
