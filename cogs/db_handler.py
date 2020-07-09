#!/usr/bin/env python3.6
from discord.ext import commands, tasks
import discord, os, asyncio
import copy, asyncpg, json

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
        }

        for key in entry.keys():
            cmd[key] = entry[key]

        return cmd

    async def get_dbs(self):
        starboard_db = await self.fetch_table("starboard")
        config_db = await self.fetch_table("seraphim_config")

        starboard_dict = {}
        config_dict = {}

        for row in starboard_db:
            starboard_dict[row["ori_mes_id"]] = {
                "ori_chan_id": row["ori_chan_id"],
                "star_var_id": row["star_var_id"],
                "author_id": row["author_id"],
                "ori_reactors": row["ori_reactors"] if row["ori_reactors"] != None else [],
                "var_reactors": row["var_reactors"] if row["var_reactors"] != None else [],
                "guild_id": row["guild_id"],
                "forced": bool(row["forced"]) if row["forced"] != None else False,

                "ori_mes_id_bac": row["ori_mes_id"],
                "updated": False
            }

        for row in config_db:
            config_dict[row["server_id"]] = {
                "starboard_id": row["starboard_id"],
                "star_limit": row["star_limit"],
                "star_blacklist": row["star_blacklist"] if row["star_blacklist"] != None else [],
                "star_toggle": bool(row["star_toggle"]) if row["star_toggle"] != None else False,
                "pingable_roles": row["pingable_roles"] if row["pingable_roles"] != None else {},
                "pin_config": row["pin_config"] if row["pin_config"] != None else {},

                "guild_id_bac": row["server_id"]
            }

        self.bot.starboard = starboard_dict
        self.bot.config = config_dict
        self.bot.starboard_bac = copy.deepcopy(starboard_dict)
        self.bot.config_bac = copy.deepcopy(config_dict)

    @tasks.loop(minutes=2.5)
    async def commit_loop(self):
        list_of_cmds = []
        starboard = self.bot.starboard
        star_bac = self.bot.starboard_bac

        for message in self.bot.starboard.keys():
            if starboard[message]["ori_chan_id"] == None:
                list_of_cmds.append(self.create_cmd("starboard", "DELETE FROM", starboard[message]))
                del self.bot.starboard[message]
            else:
                if message in list(star_bac.keys()):
                    if not starboard[message] == star_bac[message]:
                        list_of_cmds.append(self.create_cmd("starboard", "UPDATE", starboard[message]))
                else:
                    list_of_cmds.append(self.create_cmd("starboard", "INSERT INTO", starboard[message]))

        self.bot.starboard_bac = copy.deepcopy(self.bot.starboard)

        config = self.bot.config
        config_bac = self.bot.config_bac

        for server in self.bot.config.keys():
            if server in list(config_bac.keys()):
                if not config[server] == config_bac[server]:
                    list_of_cmds.append(self.create_cmd("seraphim_config", "UPDATE", config[server]))
            else:
                list_of_cmds.append(self.create_cmd("seraphim_config", "INSERT INTO", config[server]))
        self.bot.config_bac = copy.deepcopy(self.bot.config)

        if list_of_cmds != []:
            await self.run_commands(list_of_cmds)

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

        await conn.set_type_codec('json', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')

        data = await conn.fetch(f"SELECT * FROM {table}")
        await conn.close()
        return data

    async def run_commands(self, commands):
        db_url = os.environ.get("DB_URL")
        conn = await asyncpg.connect(db_url)

        await conn.set_type_codec('json', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')

        async with conn.transaction():
            for command in commands:
                db_command = ""

                if command["table"] == "seraphim_config":
                    if command["type"] == "INSERT INTO":
                        db_command = ("INSERT INTO seraphim_config" +
                        "(server_id, starboard_id, star_limit, star_blacklist, star_toggle, pingable_roles, pin_config) VALUES(" +
                        "$1, $2, $3, $4, $5, $6, $7)")
                    elif command["type"] == "UPDATE":
                        db_command = ("UPDATE seraphim_config SET starboard_id = $2, star_limit = $3, " +
                        "star_blacklist = $4, star_toggle = $5, pingable_roles = $6, pin_config = $7 WHERE server_id = $1")
                    
                    if db_command != "":
                        await conn.execute(db_command, command["guild_id_bac"], command["starboard_id"], command["star_limit"], 
                        command["star_blacklist"], command["star_toggle"], command["pingable_roles"], command["pin_config"])

                elif command["table"] == "starboard":
                    if command["type"] == "DELETE FROM":
                        await conn.execute("DELETE FROM starboard WHERE ori_mes_id = $1", command["ori_mes_id_bac"])
                        continue
                    elif command["type"] == "INSERT INTO":
                        db_command = ("INSERT INTO starboard" +
                        "(ori_mes_id, ori_chan_id, star_var_id, author_id, ori_reactors, var_reactors, guild_id, forced)" +
                        " VALUES($1, $2, $3, $4, $5, $6, $7, $8)")
                    elif command["type"] == "UPDATE":
                        db_command = ("UPDATE starboard SET ori_chan_id = $2, star_var_id = $3, ori_reactors = $5, " +
                        f"var_reactors = $6, guild_id = $7, forced = $8, " +
                        f"author_id = $4 WHERE ori_mes_id = $1")

                    if db_command != "":
                        await conn.execute(db_command, command["ori_mes_id_bac"], command["ori_chan_id"], command["star_var_id"], 
                        command["author_id"], command["ori_reactors"], command["var_reactors"], command["guild_id"],
                        command["forced"])

        await conn.close()
    
def setup(bot):
    bot.add_cog(DBHandler(bot))