from discord.ext import commands
import discord

class ClearEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, mes):
        mes_log_messages = [v for v in self.bot.mes_log[str(mes.guild.id)].values()]
        star_variant = [m["mes"] for m in mes_log_messages if mes.id == m["mes"].id]
        if star_variant == []:
            star_variant = [m["mes"] for m in mes_log_messages if str(mes.id) in m["mes"].content] 

        if star_variant != []:
            self.bot.mes_log[str(mes.guild.id)].remove(mes.id)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        message_ids = [m.id for m in messages]

        mes_log_messages = [v for v in self.bot.mes_log[str(messages[0].guild.id)].values()]
        star_variants = [m["mes"] for m in mes_log_messages if m["mes"].id in message_ids]

        for message_id in message_ids:
            star_variants_append = [m["mes"] for m in mes_log_messages if str(message_id) in m["mes"].content]

            if star_variants_append != []:
                star_variants.append(star_variants_append[0])

        if star_variants != []:
            for star_variant in star_variants:
                del self.bot.mes_log[str(messages[0].guild.id)][star_variant["mes"].id]

    @commands.Cog.listener()
    async def on_reaction_clear(self, mes, reactions):
        mes_log_messages = [v for v in self.bot.mes_log[str(mes.guild.id)].values()]
        star_variant = [m["mes"] for m in mes_log_messages if mes.id == m["mes"].id]
        if star_variant == []:
            star_variant = [m["mes"] for m in mes_log_messages if str(mes.id) in m["mes"].content]

        if star_variant != []:
            await star_variant[0].delete()
            del self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]

    @commands.Cog.listener()
    async def on_reaction_clear_emoji(self, reaction):
        if str(reaction) == "⭐":
            mes = reaction.message

            mes_log_messages = [v for v in self.bot.mes_log[str(mes.guild.id)].values()]
            star_variant = [m["mes"] for m in mes_log_messages if mes.id == m["mes"].id]
            if star_variant == []:
                star_variant = [m["mes"] for m in mes_log_messages if str(mes.id) in m["mes"].content] 

            if star_variant != []:
                await star_variant[0].delete()
                del self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]


def setup(bot):
    bot.add_cog(ClearEvents(bot))