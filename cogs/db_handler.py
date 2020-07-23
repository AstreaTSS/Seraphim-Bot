#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import discord, os, asyncio, importlib
import copy, asyncpg, json

import common.utils as utils

class DBHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commit_loop.start()

    def cog_unload(self):
        self.commit_loop.cancel()

    def create_cmd(self, table, a_type, entry):
        cmd = {
            "table": table,
            "type": a_type,
            "entry": entry
        }

        return cmd

    async def get_dbs(self):
        starboard_db = await self.fetch_table("starboard")
        config_db = await self.fetch_table("seraphim_config")

        starboard_dict = {}
        config_dict = {}

        for row in starboard_db:
            starboard_dict[row["ori_mes_id"]] = row["data"]
            starboard_dict[row["ori_mes_id"]]["updated"] = False

        for row in config_db:
            config_dict[row["guild_id"]] = row["config"]

        self.bot.starboard = starboard_dict
        self.bot.config = config_dict
        self.bot.starboard_bac = copy.deepcopy(starboard_dict)
        self.bot.config_bac = copy.deepcopy(config_dict)

    @tasks.loop(minutes=2.5)
    async def commit_loop(self):
        list_of_cmds = []

        starboard = self.bot.starboard
        star_bac = self.bot.starboard_bac

        for message in list(self.bot.starboard.keys()).copy():
            if starboard[message]["ori_chan_id"] == None:
                list_of_cmds.append(self.create_cmd("starboard", "DELETE FROM", starboard[message]))
                del self.bot.starboard[message]
            else:
                if message in list(star_bac.keys()):
                    if not starboard[message] == star_bac[message]:
                        list_of_cmds.append(self.create_cmd("starboard", "UPDATE", starboard[message]))
                else:
                    list_of_cmds.append(self.create_cmd("starboard", "INSERT INTO", starboard[message]))

        config = self.bot.config
        config_bac = self.bot.config_bac

        for guild in list(self.bot.config.keys()).copy():
            if guild in list(config_bac.keys()):
                if not config[guild] == config_bac[guild]:
                    list_of_cmds.append(self.create_cmd("seraphim_config", "UPDATE", config[guild]))
            else:
                list_of_cmds.append(self.create_cmd("seraphim_config", "INSERT INTO", config[guild]))

        if list_of_cmds != []:
            await self.run_commands(list_of_cmds)

            self.bot.starboard_bac = copy.deepcopy(self.bot.starboard)
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

        await asyncio.sleep(60)

    async def fetch_table(self, table):
        db_url = os.environ.get("DB_URL")
        conn = await asyncpg.connect(db_url)

        await conn.set_type_codec('jsonb', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')

        data = await conn.fetch(f"SELECT * FROM {table}")
        await conn.close()
        return data

    async def run_commands(self, commands):
        db_url = os.environ.get("DB_URL")
        conn = await asyncpg.connect(db_url)

        await conn.set_type_codec('jsonb', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')

        async with conn.transaction():
            for command in commands:
                db_command = ""

                if command["table"] == "seraphim_config":
                    if command["type"] == "INSERT INTO":
                        db_command = ("INSERT INTO seraphim_config(guild_id, config) VALUES($1, $2)")
                    elif command["type"] == "UPDATE":
                        db_command = ("UPDATE seraphim_config SET config = $2 WHERE guild_id = $1")
                    
                    if db_command != "":
                        await conn.execute(db_command, command["entry"]["guild_id_bac"], command["entry"])

                elif command["table"] == "starboard":
                    if command["type"] == "DELETE FROM":
                        await conn.execute("DELETE FROM starboard WHERE ori_mes_id = $1", command["entry"]["ori_mes_id_bac"])
                        continue
                    elif command["type"] == "INSERT INTO":
                        db_command = ("INSERT INTO starboard(ori_mes_id, data) VALUES($1, $2)")
                    elif command["type"] == "UPDATE":
                        db_command = ("UPDATE starboard SET data = $2 WHERE ori_mes_id = $1")

                    if db_command != "":
                        await conn.execute(db_command, command["entry"]["ori_mes_id_bac"], command["entry"])

        await conn.close()
    
def setup(bot):
    importlib.reload(utils)
    bot.add_cog(DBHandler(bot))