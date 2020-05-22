from discord.ext import commands
import discord

class OwnerCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def author_from_embed(self, mes):
        embed = mes.embeds[0]
        basic_author = embed.author.name.split("#")
        author = discord.utils.get(mes.guild.members, name=basic_author[0], discriminator=basic_author[1])
        return mes.author.id if author == None else None

    @commands.command()
    @commands.is_owner()
    async def sync_dank(self, ctx):
        await ctx.send("Starting sync. This might take a while.")

        for key in self.bot.starboard.keys():
            entry = self.bot.starboard[key]
            if entry["author_id"] in [270904126974590976, 499383056822435840]:
                guild = self.bot.get_guild(entry["guild_id"])
                
                if entry["star_var_id"] != None:
                    starboard_id = self.bot.star_config[guild.id]['starboard_id']
                    star_chan = guild.get_channel(starboard_id)
                    if star_chan != None:
                        try:
                            star_mes = await star_chan.fetch_message(entry["star_var_id"])
                            author_id = self.author_from_embed(star_mes)
                            if author_id != None:
                                self.bot.starboard[key]["author_id"] = author_id
                        except discord.NotFound:
                            do_nothing = True

                else:
                    ori_chan = guild.get_channel(entry['ori_chan_id'])
                    if ori_chan != None:
                        try:
                            ori_mes = await ori_chan.fetch_message(key)
                            author_id = self.author_from_embed(ori_mes)
                            if author_id != None:
                                self.bot.starboard[key]["author_id"] = author_id
                        except discord.NotFound:
                            do_nothing = True

        await ctx.send("Sync done! You can now unload this cog.")

def setup(bot):
    bot.add_cog(OwnerCMDs(bot))