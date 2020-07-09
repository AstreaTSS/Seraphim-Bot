#!/usr/bin/env python3.6
from discord.ext import commands
import discord, importlib

import common.star_utils as star_utils

class ClearEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def auto_clear_stars(self, bot, payload):
        star_variant = star_utils.get_star_entry(self.bot, payload.message_id)
        if star_variant != []:
            star_utils.clear_stars(self.bot, star_variant, payload.message_id)
            await star_utils.star_entry_refresh(self.bot, star_variant, payload.guild_id)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if not star_utils.star_check(self.bot, payload):
            return
        
        star_variant = star_utils.get_star_entry(self.bot, payload.message_id)

        if star_variant != []:
            ori_mes_id = star_variant["ori_mes_id_bac"]
            if star_variant["star_var_id"] != payload.message_id:
                self.bot.starboard[ori_mes_id]["ori_chan_id"] = None
            else:
                self.bot.starboard[ori_mes_id]["star_var_id"] = None
                self.bot.starboard[ori_mes_id]["forced"] = False

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        if not star_utils.star_check(self.bot, payload):
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
        if not star_utils.star_check(self.bot, payload):
            return

        await self.auto_clear_stars(self.bot, payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload):
        if not star_utils.star_check(self.bot, payload):
            return
            
        if str(payload.emoji) == "⭐":
            await self.auto_clear_stars(self.bot, payload)

def setup(bot):
    importlib.reload(star_utils)
    bot.add_cog(ClearEvents(bot))