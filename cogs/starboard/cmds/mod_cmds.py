#!/usr/bin/env python3.6
from discord.ext import commands
import discord, importlib

import common.star_utils as star_utils
import common.utils as utils
import common.star_mes_handler as star_mes

class ModCMDs(commands.Cog, name = "Mod Star"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(utils.proper_permissions)
    async def force(self, ctx, msg: discord.Message):
        """Forces a message onto the starboard, regardless of how many stars it has.
        The message represented by the message id must be in the same channel as the channel you send the command.
        This message cannot be taken off the starboard unless it is deleted from it manually.
        You must have Manage Server permissions or higher to run this command."""
        
        if not self.bot.config[ctx.guild.id]["star_toggle"]:
            await ctx.send("Starboard is not turned on for this server!")
            return

        starboard_entry = star_utils.get_star_entry(self.bot, msg.id)
        if starboard_entry == []:
            author_id = star_utils.get_author_id(msg, self.bot)
            prev_reactors = await star_utils.get_prev_reactors(msg, author_id)

            self.bot.starboard[msg.id] = {
                "ori_chan_id": msg.channel.id,
                "star_var_id": None,
                "author_id": author_id,
                "ori_reactors": prev_reactors,
                "var_reactors": [],
                "guild_id": msg.guild.id,
                "forced": False,

                "ori_mes_id_bac": msg.id,
                "updated": True
            }
            starboard_entry = self.bot.starboard[msg.id]
        
        if starboard_entry["star_var_id"] == None:
            starboard_entry["forced"] == True
        else:
            await ctx.send("This message is already on the starboard!")
            return
        
        unique_stars = star_utils.get_num_stars(starboard_entry)
        await star_mes.send(self.bot, msg, unique_stars, forced=True)

        await ctx.send("Done!")

def setup(bot):
    importlib.reload(star_utils)
    importlib.reload(utils)
    importlib.reload(star_mes)
    
    bot.add_cog(ModCMDs(bot))