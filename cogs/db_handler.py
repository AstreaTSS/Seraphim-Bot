#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import discord, os, asyncio, aiomysql, copy

class DBHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commit_loop.start()

    async def get_dbs(self):
        starboard_db = await self.run_command("SELECT * FROM starboard")
        star_config_db = await self.run_command("SELECT * FROM starboard_config")

        starboard_dict = {}
        star_config_dict = {}

        for row in starboard_db:
            starboard_dict[row[0]] = {
                "ori_chan_id": row[1],
                "star_var_id": row[2],
                "author_id": row[3],
                "ori_reactors": row[4] if row[4] != None else "",
                "var_reactors": row[5] if row[5] != None else "",
                "guild_id": row[6],
                "forced": bool(row[7]) if row[7] != None else False,

                "ori_mes_id_bac": row[0]
            }

        for row in star_config_db:
            star_config_dict[row[0]] = {
                "starboard_id": row[1],
                "star_limit": row[2],
                "blacklist": row[3] if row[3] != None else "",
                "guild_id_bac": row[0]
            }

        self.bot.starboard = starboard_dict
        self.bot.star_config = star_config_dict
        self.bot.starboard_bac = copy.deepcopy(starboard_dict)
        self.bot.star_config_bac = copy.deepcopy(star_config_dict)

    @tasks.loop(minutes=2.5)
    async def commit_loop(self):
        list_of_cmds = []
        starboard = self.bot.starboard
        star_bac = self.bot.starboard_bac

        for message in starboard.keys():
            if starboard[message]["ori_chan_id"] == None:
                list_of_cmds.append(f"DELETE FROM starboard WHERE ori_mes_id = {message}")
                del starboard[message]
            else:
                star_var_id = starboard[message]["star_var_id"] if starboard[message]["star_var_id"] != None else "NULL"
                guild_id = starboard[message]["guild_id"] if starboard[message]["guild_id"] != None else "NULL"
                ori_reactors = f"'{starboard[message]['ori_reactors']}'" if starboard[message]['ori_reactors'] != "" else "NULL"
                var_reactors = f"'{starboard[message]['var_reactors']}'" if starboard[message]['var_reactors'] != "" else "NULL"
                forced = starboard[message]["forced"] if starboard[message]["forced"] != None else "NULL"

                if message in star_bac.keys():
                    if not starboard[message] == star_bac[message]:
                        list_of_cmds.append(f"UPDATE starboard SET star_var_id = {star_var_id}, ori_reactors = {ori_reactors}, " +
                        f"var_reactors = {var_reactors}, guild_id = {guild_id}, forced = {forced}, " +
                        f"author_id = {starboard[message]['author_id']} WHERE ori_mes_id = {message}")
                else:
                    list_of_cmds.append("INSERT INTO starboard "+
                    "(ori_mes_id, ori_chan_id, star_var_id, author_id, ori_reactors, var_reactors, guild_id, forced) VALUES " +
                    f"({message}, {starboard[message]['ori_chan_id']}, {star_var_id}, " +
                    f"{starboard[message]['author_id']}, {ori_reactors}, {var_reactors}, {guild_id}, {forced});")
        self.bot.starboard_bac = copy.deepcopy(self.bot.starboard)

        star_config = self.bot.star_config
        star_config_bac = self.bot.star_config_bac

        for server in star_config.keys():
            if server in star_config_bac.keys():
                if not star_config[server] == star_config_bac[server]:
                    blacklist = f"'{star_config[server]['blacklist']}'" if star_config[server]['blacklist'] != "" else "NULL"

                    list_of_cmds.append(f"UPDATE starboard_config SET starboard_id = {star_config[server]['starboard_id']}, " + 
                    f"star_limit = {star_config[server]['star_limit']}, blacklist = {blacklist} WHERE server_id = {server}")
        self.bot.star_config_bac = copy.deepcopy(self.bot.star_config)

        if list_of_cmds != []:
            await self.run_command(list_of_cmds, a_list = True, commit = True)

    @commit_loop.before_loop
    async def before_commit_loop(self):
        if self.bot.init_load:
            await self.get_dbs()

            while self.bot.star_config == {} or self.bot.starboard == {}:
                await asyncio.sleep(0.1)

        await asyncio.sleep(60)

    async def run_command(self, command, a_list = False, commit = False):
        output = None

        host = os.environ.get("DB_HOST_URL")
        port = os.environ.get("DB_PORT")
        username = os.environ.get("DB_USERNAME")
        password = os.environ.get("DB_PASSWORD")
        db = os.environ.get("DB_NAME")

        pool = await aiomysql.create_pool(host=host, port=int(port),
                                          user=username, password=password,
                                          db=db)

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                if a_list:
                    for a_command in command:
                        await cur.execute(a_command)
                else:
                    await cur.execute(command)

                if commit:
                    await conn.commit()
                output = await cur.fetchall()
                
        pool.close()
        await pool.wait_closed()

        return output
    
def setup(bot):
    bot.add_cog(DBHandler(bot))