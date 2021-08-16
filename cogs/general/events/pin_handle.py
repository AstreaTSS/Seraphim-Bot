import importlib

import discord
from discord.ext import commands

import common.star_mes_handler as star_mes
import common.utils as utils


class PinHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.type != discord.MessageType.pins_add or not msg.guild:
            return

        pin_config = self.bot.config.getattr(msg.guild.id, "pin_config")
        chan_entry = pin_config.get(str(msg.channel.id))
        if not chan_entry:
            chan_entry = pin_config.get("default")
        if not chan_entry:
            return

        pins = await msg.channel.pins()
        await utils.msg_to_owner(self.bot, pins)

        if len(pins) > chan_entry["limit"]:

            entry = pins[-1] if not chan_entry["reversed"] else pins[0]
            des_chan = msg.guild.get_channel(chan_entry["destination"])
            if des_chan is None:
                return

            send_embed = await star_mes.star_generate(self.bot, entry)
            send_embed.color = discord.Colour.default()

            await des_chan.send(embed=send_embed)
            await entry.unpin()


def setup(bot):
    importlib.reload(utils)
    importlib.reload(star_mes)

    bot.add_cog(PinHandler(bot))
