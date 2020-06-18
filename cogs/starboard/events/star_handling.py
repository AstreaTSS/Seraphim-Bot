#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib

import bot_utils.universals as univ
import bot_utils.star_universals as star_univ
import bot_utils.star_mes_handler as star_mes

class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(univ)
        importlib.reload(star_univ)
        importlib.reload(star_mes)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not (star_univ.star_check(self.bot, payload) and str(payload.emoji) == "⭐"):
            return

        try:
            user, channel, mes = await univ.fetch_needed(self.bot, payload)
        except discord.HTTPException:
            univ.msg_to_owner(self.bot, f"{payload.message_id}: could not find Message object. Channel: {payload.channel_id}")
            return

        if (not user.bot and mes.author.id != user.id
            and not channel.id in self.bot.config[mes.guild.id]["star_blacklist"]):

            star_variant = star_univ.get_star_entry(self.bot, mes.id, check_for_var=True)

            if star_variant == []:
                if channel.id != self.bot.config[mes.guild.id]["starboard_id"]:
                    await star_univ.modify_stars(self.bot, mes, payload.user_id, "ADD")

                    star_entry = star_univ.get_star_entry(self.bot, mes.id)
                    unique_stars = star_univ.get_num_stars(star_entry)

                    if unique_stars >= self.bot.config[mes.guild.id]["star_limit"]:
                        await star_mes.send(self.bot, mes, unique_stars)

                elif mes.embeds != []:
                    if user.id == self.bot.user.id:
                        entry = await star_univ.import_old_entry(self.bot, mes)
                        if entry != None:
                            await star_univ.star_entry_refresh(self.bot, entry, mes.guild.id)
                            
            elif user.id != star_variant["author_id"]:
                await star_univ.modify_stars(self.bot, mes, payload.user_id, "ADD")
                await star_univ.star_entry_refresh(self.bot, star_variant, mes.guild.id)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not (star_univ.star_check(self.bot, payload) and str(payload.emoji) == "⭐"):
            return
            
        try:
            user, channel, mes = await univ.fetch_needed(self.bot, payload)
        except discord.NotFound:
            return

        if (not user.bot and mes.author.id != user.id
            and not channel.id in self.bot.config[mes.guild.id]["star_blacklist"]):

            star_variant = star_univ.get_star_entry(self.bot, mes.id)

            if star_variant != []:
                await star_univ.modify_stars(self.bot, mes, payload.user_id, "SUBTRACT")

                if star_variant["star_var_id"] != None:
                    await star_univ.star_entry_refresh(self.bot, star_variant, mes.guild.id)
        
def setup(bot):
    bot.add_cog(Star(bot))