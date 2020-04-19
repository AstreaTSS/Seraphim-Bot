from discord.ext import commands
import discord
import cogs.interact_db as db

class ClearEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, mes):
        star_variant = await db.run_command("SELECT * FROM starboard WHERE " +
        f"(ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}') AND " +
        f"star_var_id IS NOT NULL;")  

        if star_variant != ():
            await db.run_command(f"DELETE FROM starboard WHERE star_var_id = '{star_variant[0][2]}")

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        message_ids = [m.id for m in messages]
        star_variants = []

        for message_id in message_ids:
            star_variant = await db.run_command("SELECT * FROM starboard WHERE " +
            f"(ori_mes_id = '{message_id}' OR star_var_id = '{message_id}') AND " +
            f"star_var_id IS NOT NULL;")

            if star_variant != ():
                star_variants.append(star_variant[0])

        if star_variants != ():
            for star_variant in star_variants:
                await db.run_command(f"DELETE FROM starboard WHERE star_var_id = '{star_variant[2]}")

    @commands.Cog.listener()
    async def on_reaction_clear(self, mes, reactions):
        config_file = await db.run_command(f"SELECT * FROM starboard_config WHERE server_id = {mes.guild.id}")

        star_variant = await db.run_command("SELECT * FROM starboard WHERE " +
            f"(ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}') AND " +
            f"star_var_id IS NOT NULL;")

        if star_variant != ():
            star_var_chan = await self.bot.fetch_channel(config_file[0][0])
            star_var_mes = await star_var_chan.fetch_message(star_variant[0][2])

            await star_var_mes.delete()
            await db.run_command(f"DELETE FROM starboard WHERE star_var_id = '{star_variant[0][2]}")

    @commands.Cog.listener()
    async def on_reaction_clear_emoji(self, reaction):
        if str(reaction) == "⭐":
            mes = reaction.message
            config_file = await db.run_command(f"SELECT * FROM starboard_config WHERE server_id = {mes.guild.id}")
            
            star_variant = await db.run_command("SELECT * FROM starboard WHERE " +
            f"(ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}') AND " +
            f"star_var_id IS NOT NULL;")

            if star_variant != ():
                star_var_chan = await self.bot.fetch_channel(config_file[0][0])
                star_var_mes = await star_var_chan.fetch_message(star_variant[0][2])

                await star_var_mes.delete()
                await db.run_command(f"DELETE FROM starboard WHERE star_var_id = '{star_variant[0][2]}")

def setup(bot):
    bot.add_cog(ClearEvents(bot))