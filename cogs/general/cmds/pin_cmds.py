from discord.ext import commands
import discord, importlib

import common.utils as utils
import common.star_mes_handler as star_mes

class PinCMDs(commands.Cog, name = "Pinboard"):
    """Commands for the pinboard. See the settings command to set a pinboard up."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ["pin_all"])
    @commands.check(utils.proper_permissions)
    async def pinall(self, ctx):
        """Retroactively moves overflowing pins from the channel this command is used in to the destination channel.
        Useful if you just mapped a channel and need to move old pin entries.
        Requires Manage Server permissions or higher."""

        if not str(ctx.channel.id) in self.bot.config[ctx.guild.id]["pin_config"].keys():
            await ctx.send("This channel isn't mapped!")
            return

        chan_entry = self.bot.config[ctx.guild.id]["pin_config"][str(ctx.channel.id)]

        pins = await ctx.channel.pins()
        pins.reverse() # pins are retrived newest -> oldest, we want to do the opposite

        if not len(pins) > chan_entry["limit"]:
            await ctx.send("The number of pins is below or at the limit!")
            return

        des_chan = self.bot.get_channel(chan_entry["destination"])
        if des_chan == None:
            await ctx.send("The destination channel doesn't exist anymore!")
            return

        dif = len(pins) - chan_entry["limit"]
        pins_subset = pins[-dif:]

        for pin in pins_subset:
            send_embed = await star_mes.star_generate(self.bot, pin)
            send_embed.color = discord.Colour.default()

            await des_chan.send(embed = send_embed)
            await pin.unpin()

        await ctx.send("Done!")

def setup(bot):
    importlib.reload(utils)
    importlib.reload(star_mes)
    
    bot.add_cog(PinCMDs(bot))