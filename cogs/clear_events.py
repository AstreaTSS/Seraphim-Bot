from discord.ext import commands
import discord

class ClearEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def star_updater(self, payload, star_variant):
        if payload.message_id == star_variant[0]["var_reactors"]:
            star_variant[0]["var_reactors"] = ""
        else:
            star_variant[0]["ori_reactors"] = ""

        ori_reactors = star_variant[0]["ori_reactors"].split(",")
        var_reactors = star_variant[0]["var_reactors"].split(",")
        reactors = [i for i in ori_reactors if i != ""] + [i for i in var_reactors if i != ""]

        star_var_chan = await self.bot.fetch_channel(self.bot.star_config[payload.guild_id]["starboard_id"])
        star_var_mes = await star_var_chan.fetch_message(star_variant[0]["star_var_id"])

        if len(reactors) < self.bot.star_config[payload.guild_id]["star_limit"]:
            await star_var_mes.delete()
            star_variant[0]["star_var_id"] = None
        else:
            ori_starred = star_var_mes.embeds[0]
            parts = star_var_mes.content.split(" | ")
            
            await star_var_mes.edit(content=f"⭐ {len(reactors)} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)

        ori_mes_id = star_variant[0]["ori_mes_id_bac"]
        self.bot.starboard[ori_mes_id] = star_variant[0]

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        star_variant = [
            self.bot.starboard[int(k)] for k in self.bot.starboard.keys()
            if (int(k) == payload.message_id or self.bot.starboard[int(k)]["star_var_id"] == payload.message_id)
            and self.bot.starboard[int(k)]["star_var_id"] != None
        ]

        if star_variant != []:
            ori_mes_id = star_variant[0]["ori_mes_id_bac"]
            self.bot.starboard[ori_mes_id]["ori_chan_id"] = None

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        star_variants = [
            self.bot.starboard[k] for k in self.bot.starboard.keys()
            if (int(k) in payload.message_ids or self.bot.starboard[int(k)]["star_var_id"] in payload.message_ids)
        ]

        if star_variants != []:
            for star_variant in star_variants:
                ori_mes_id = star_variant[0]["ori_mes_id_bac"]
                self.bot.starboard[ori_mes_id]["ori_chan_id"] = None

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        star_variant = [
            self.bot.starboard[int(k)] for k in self.bot.starboard.keys()
            if (int(k) == payload.message_id or self.bot.starboard[int(k)]["star_var_id"] == payload.message_id)
            and self.bot.starboard[int(k)]["star_var_id"] != None
        ]

        if star_variant != []:
            await self.star_updater(payload, star_variant)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload):
        if str(payload.emoji) == "⭐":
            star_variant = [
                self.bot.starboard[int(k)] for k in self.bot.starboard.keys()
                if (int(k) == payload.message_id or self.bot.starboard[int(k)]["star_var_id"] == payload.message_id)
                and self.bot.starboard[int(k)]["star_var_id"] != None
            ]

            if star_variant != []:
                await self.star_updater(payload, star_variant)

def setup(bot):
    bot.add_cog(ClearEvents(bot))