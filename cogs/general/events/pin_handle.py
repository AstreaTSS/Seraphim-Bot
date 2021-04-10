import importlib

import discord
from discord.ext import commands

import common.star_mes_handler as star_mes
import common.utils as utils


class PinHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        if not msg.type == discord.MessageType.pins_add or not msg.guild:
            return

        pin_config = self.bot.config.getattr(msg.guild.id, "pin_config")
        chan_entry = pin_config.get(str(msg.channel.id))
        if not chan_entry:
            chan_entry = pin_config.get("default")
            if not chan_entry:
                return

        pins = await msg.channel.pins()

        if len(pins) > chan_entry["limit"]:
            early_entry = pins[-1]

            des_chan = self.bot.get_channel(chan_entry["destination"])
            if des_chan == None:
                return

            send_embed = await star_mes.star_generate(self.bot, early_entry)
            send_embed.color = discord.Colour.default()

            await des_chan.send(embed=send_embed)
            await early_entry.unpin()


def setup(bot):
    importlib.reload(utils)
    importlib.reload(star_mes)

    bot.add_cog(PinHandler(bot))
