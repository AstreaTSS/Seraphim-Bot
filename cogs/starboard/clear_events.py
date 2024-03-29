#!/usr/bin/env python3.8
import importlib

import discord
from discord.ext import commands

import common.star_utils as star_utils
import common.utils as utils


class ClearEvents(commands.Cog):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    async def auto_clear_stars(self, payload):
        star_variant = await self.bot.starboard.get(payload.message_id)
        if star_variant:
            star_utils.clear_stars(self.bot, star_variant, payload.message_id)
            await star_utils.star_entry_refresh(
                self.bot, star_variant, payload.guild_id
            )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if not star_utils.star_check(self.bot, payload):
            return

        star_variant = await self.bot.starboard.get(payload.message_id)

        if star_variant:
            if star_variant.star_var_id != payload.message_id:
                self.bot.starboard.delete(star_variant.ori_mes_id)

                if star_variant.star_var_id != None:
                    star_chan = self.bot.get_partial_messageable(
                        star_variant.starboard_id
                    )
                    try:
                        star_mes = await star_chan.fetch_message(
                            star_variant.star_var_id
                        )
                        await star_mes.delete()
                        self.bot.star_queue.remove_from_copy(
                            (
                                star_variant.ori_chan_id,
                                star_variant.ori_mes_id,
                                star_variant.guild_id,
                            )
                        )
                    except discord.HTTPException:
                        pass
            else:
                star_variant.star_var_id = None
                star_variant.starboard_id = None
                star_variant.forced = False
                self.bot.starboard.upsert(star_variant)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        if not star_utils.star_check(self.bot, payload):
            return

        init_star_variants = [
            await self.bot.starboard.get(k) for k in payload.message_ids
        ]
        star_variants = [k for k in init_star_variants if k != None]

        if star_variants != []:
            for star_variant in star_variants:
                if star_variant.star_var_id not in payload.message_ids:
                    self.bot.starboard.delete(star_variant.ori_mes_id)

                    if star_variant.star_var_id != None:
                        star_chan = self.bot.get_partial_messageable(
                            star_variant.starboard_id
                        )
                        try:
                            star_mes = await star_chan.fetch_message(
                                star_variant.star_var_id
                            )
                            await star_mes.delete()
                            self.bot.star_queue.remove_from_copy(
                                (
                                    star_variant.ori_chan_id,
                                    star_variant.ori_mes_id,
                                    star_variant.guild_id,
                                )
                            )
                        except discord.HTTPException:
                            pass
                else:
                    star_variant.star_var_id = None
                    star_variant.starboard_id = None
                    star_variant.forced = False
                    self.bot.starboard.upsert(star_variant)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        if not star_utils.star_check(self.bot, payload):
            return

        await self.auto_clear_stars(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload):
        if not star_utils.star_check(self.bot, payload):
            return

        if str(payload.emoji) == "⭐":
            await self.auto_clear_stars(payload)


async def setup(bot):
    importlib.reload(utils)
    importlib.reload(star_utils)
    await bot.add_cog(ClearEvents(bot))
