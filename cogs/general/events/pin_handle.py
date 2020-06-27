from discord.ext import commands
import discord

import bot_utils.universals as univ
import bot_utils.star_mes_handler as star_mes

class PinHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        if (not msg.type == discord.MessageType.pins_add) or msg.guild == None:
            return

        if not str(msg.channel.id) in self.bot.config[msg.guild.id]["pin_config"].keys():
            return

        chan_entry = self.bot.config[msg.guild.id]["pin_config"][str(msg.channel.id)]

        pins = await msg.channel.pins()

        if len(pins) > chan_entry["limit"]:
            early_entry = pins[-1]

            des_chan = self.bot.get_channel(chan_entry["destination"])
            if des_chan == None:
                return

            send_embed = await star_mes.generate(self.bot, early_entry)
            send_embed.color = discord.Colour(0x4378fc)

            await des_chan.send(embed = send_embed)
            await early_entry.unpin()

def setup(bot):
    bot.add_cog(PinHandler(bot))