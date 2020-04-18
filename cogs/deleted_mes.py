from discord.ext import commands
import discord

class DeletedMes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        guild_id = payload.guild_id
        message_id = payload.message_id

        star_variant = [m for m in self.bot.mes_log[str(guild_id)] if message_id == m.id]
        if star_variant is []:
            star_variant = [m for m in self.bot.mes_log[str(guild_id)] if str(message_id) in m.content]

        if star_variant is not []:
            index = self.bot.mes_log[str(guild_id)].index(star_variant[0])
            del self.bot.mes_log[str(guild_id)][index]

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        guild_id = payload.guild_id
        message_ids = payload.message_ids

        star_variants = [m for m in self.bot.mes_log[str(guild_id)] if m.id in message_ids]

        for message_id in message_ids:
            star_variants_append = [m for m in self.bot.mes_log[str(guild_id)] if str(message_id) in m.content]

            if star_variants_append is not []:
                star_variants.append(star_variants_append[0])

        if star_variants is not []:
            for star_variant in star_variants:
                index = self.bot.mes_log[str(guild_id)].index(star_variant)
                del self.bot.mes_log[str(guild_id)][index]


def setup(bot):
    bot.add_cog(DeletedMes(bot))