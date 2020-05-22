from discord.ext import commands
import discord
import re

class SyncCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def author_from_embed(self, mes):
        try:
            embed = mes.embeds[0]
            author_discrim = re.findall('\(([^)]+)', embed.author.name)
            if author_discrim != None:
                basic_author = author_discrim[0].split("#")
                author = discord.utils.get(mes.guild.members, name=basic_author[0], discriminator=basic_author[1])
                return mes.author.id if author == None else None
            else:
                return None
        except IndexError:
            return None

    @commands.command()
    @commands.is_owner()
    async def star_fix(self, ctx):
        await ctx.send("Starting sync. This might take a while.")

        for key in self.bot.starboard.keys():
            entry = self.bot.starboard[key]
            if entry["author_id"] in [700857077672706120]:
                guild = self.bot.get_guild(entry["guild_id"])

                if guild != None:
                    starboard_id = self.bot.star_config[guild.id]['starboard_id']
                    star_chan = guild.get_channel(starboard_id)
                    try:
                        star_mes = await star_chan.fetch_message(entry["star_var_id"])
                        author_id = self.author_from_embed(star_mes)
                        if author_id != None:
                            self.bot.starboard[key]["author_id"] = author_id
                    except discord.NotFound:
                        do_nothing = True

        await ctx.send("Sync done! You can now unload this cog.")

def setup(bot):
    bot.add_cog(SyncCMD(bot))