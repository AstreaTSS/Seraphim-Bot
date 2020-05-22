#!/usr/bin/env python3.7
from discord.ext import commands
import discord

import cogs.star_universals as star_univ

class ClearEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def auto_clear_stars(self, bot, payload):
        star_variant = star_univ.get_star_entry(self.bot, payload.message_id)
        star_univ.clear_stars(self.bot, star_variant, payload.message_id)
        await star_univ.star_entry_refresh(self.bot, star_variant, payload.guild_id)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        star_variant = star_univ.get_star_entry(self.bot, payload.message_id)

        if star_variant != []:
            ori_mes_id = star_variant["ori_mes_id_bac"]
            self.bot.starboard[ori_mes_id]["ori_chan_id"] = None

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        star_variants = [
            self.bot.starboard[k] for k in self.bot.starboard.keys()
            if (int(k) in payload.message_ids or self.bot.starboard[int(k)]["star_var_id"] in payload.message_ids)
        ]

        if star_variants != []:
            for star_variant in star_variants:
                ori_mes_id = star_variant["ori_mes_id_bac"]
                self.bot.starboard[ori_mes_id]["ori_chan_id"] = None

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        await self.auto_clear_stars(self.bot, payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload):
        if str(payload.emoji) == "⭐":
            await self.auto_clear_stars(self.bot, payload)

def setup(bot):
    bot.add_cog(ClearEvents(bot))