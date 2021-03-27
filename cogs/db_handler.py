#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import asyncio, importlib, copy

import common.utils as utils
import common.star_classes as star_classes

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

        config_dict = {}
        for row in config_db:
            config_dict[row["guild_id"]] = row["config"]

        self.bot.config = config_dict
        self.bot.config_bac = copy.deepcopy(config_dict)

    def get_required_from_entry(self, entry):
        entry.ori_reactors = list(entry.ori_reactors)
        entry.var_reactors = list(entry.var_reactors)
        
        necessary = (entry.ori_mes_id, entry.to_dict())

        entry.ori_reactors = set(entry.ori_reactors)
        entry.var_reactors = set(entry.var_reactors)
        
        return necessary

    @tasks.loop(minutes=2.5)
    async def commit_loop(self):
        insert_config = []
        update_config = []
        delete_sb = []
        insert_sb = []
        update_sb = []

        for entry_id in self.bot.starboard.added:
            entry = self.bot.starboard.get(entry_id)
            insert_sb.append(self.get_required_from_entry(entry))

        for entry_id in self.bot.starboard.updated:
            entry = self.bot.starboard.get(entry_id)
            update_sb.append(self.get_required_from_entry(entry))

        for entry_id in self.bot.starboard.removed:
            delete_sb.append(entry_id)

        self.bot.starboard.reset_deltas()

        config = self.bot.config
        config_bac = self.bot.config_bac

        for guild in list(self.bot.config.keys()).copy():
            if guild in list(config_bac.keys()):
                if not config[guild] == config_bac[guild]:
                    update_config.append((config["guild"]["guild_id_bac"], config["guild"]))
            else:
                insert_config.append((config["guild"]["guild_id_bac"], config["guild"]))

        if insert_config or update_config or delete_sb or insert_sb or update_sb:
            await self.update_db(insert_config, update_config, delete_sb, insert_sb, update_sb)

            self.bot.config_bac = copy.deepcopy(self.bot.config)

    @commit_loop.error
    async def error_handle(self, *args):
        error = args[-1]
        await utils.error_handle(self.bot, error)

    @commit_loop.before_loop
    async def before_commit_loop(self):
        if self.bot.init_load:
            await self.get_dbs()

            while self.bot.config == {}:
                await asyncio.sleep(0.1)

        await asyncio.sleep(90)

    async def fetch_table(self, table):
        async with self.bot.pool.acquire() as conn:
            data = await conn.fetch(f"SELECT * FROM {table}")

        return data

    async def update_db(self, insert_config, update_config, delete_sb, insert_sb, update_sb):
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                if insert_config:
                    await conn.executemany("INSERT INTO seraphim_config(guild_id, config) VALUES($1, $2)", args=insert_config)
                if update_config:
                    await conn.executemany("UPDATE seraphim_config SET config = $2 WHERE guild_id = $1", args=update_config)

                if delete_sb:
                    await conn.executemany("DELETE FROM starboard WHERE ori_mes_id = $1", args=delete_sb)
                if insert_sb:
                    await conn.executemany("INSERT INTO starboard(ori_mes_id, data) VALUES($1, $2)", args=insert_sb)
                if update_sb:
                    await conn.executemany("UPDATE starboard SET data = $2 WHERE ori_mes_id = $1", args=update_sb)
    
def setup(bot):
    importlib.reload(utils)
    bot.add_cog(DBHandler(bot))