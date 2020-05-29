#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib

import bot_utils.star_universals as star_univ

class ClearEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(star_univ)

    async def auto_clear_stars(self, bot, payload):
        star_variant = star_univ.get_star_entry(self.bot, payload.message_id)
        if star_variant != []:
            star_univ.clear_stars(self.bot, star_variant, payload.message_id)
            await star_univ.star_entry_refresh(self.bot, star_variant, payload.guild_id)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if star_univ.star_check(self.bot, payload):
            return
        
        star_variant = star_univ.get_star_entry(self.bot, payload.message_id)

        if star_variant != []:
            ori_mes_id = star_variant["ori_mes_id_bac"]
            if star_variant["star_var_id"] != payload.message_id:
                self.bot.starboard[ori_mes_id]["ori_chan_id"] = None
            else:
                self.bot.starboard[ori_mes_id]["star_var_id"] = None
                self.bot.starboard[ori_mes_id]["forced"] = False

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        if star_univ.star_check(self.bot, payload):
            return

        star_variants = [
            self.bot.starboard[k] for k in self.bot.starboard.keys()
            if (int(k) in payload.message_ids or self.bot.starboard[int(k)]["star_var_id"] in payload.message_ids)
        ]

        if star_variants != []:
            for star_variant in star_variants:
                ori_mes_id = star_variant["ori_mes_id_bac"]
                if not star_variant["star_var_id"] in payload.message_ids:
                    self.bot.starboard[ori_mes_id]["ori_chan_id"] = None
                else:
                    self.bot.starboard[ori_mes_id]["star_var_id"] = None
                    self.bot.starboard[ori_mes_id]["forced"] = False

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        if star_univ.star_check(self.bot, payload):
            return

        await self.auto_clear_stars(self.bot, payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload):
        if star_univ.star_check(self.bot, payload):
            return
            
        if str(payload.emoji) == "⭐":
            await self.auto_clear_stars(self.bot, payload)

def setup(bot):
    bot.add_cog(ClearEvents(bot))