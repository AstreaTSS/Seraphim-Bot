from discord.ext import commands
import discord, importlib

import star_utils.universals as univ

class BlacklistCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(univ)

    @commands.group()
    @commands.check(univ.proper_permissions)
    async def blacklist(self, ctx):
        if ctx.invoked_subcommand == None:
            list_cmd = self.bot.get_command("blacklist list")
            await ctx.invoke(list_cmd)

    @blacklist.command(name = "list")
    @commands.check(univ.proper_permissions)
    async def _list(self, ctx):
        channel_id_list = [int(c) for c in self.bot.star_config[ctx.guild.id]["blacklist"].split(",") if c != ""]
        if channel_id_list != []:
            channel_mentions = []

            for channel_id in channel_id_list:
                channel = await self.bot.fetch_channel(channel_id)
                channel_mentions.append(channel.mention)

            await ctx.send(f"Blacklisted channels: {', '.join(channel_mentions)}")
        else:
            await ctx.send("There's no blacklisted channels for this guild!")

    @blacklist.command()
    @commands.check(univ.proper_permissions)
    async def add(self, ctx, channel: discord.TextChannel):
        channel_id_list = [int(c) for c in self.bot.star_config[ctx.guild.id]["blacklist"].split(",") if c != ""]

        if not channel.id in channel_id_list:
            channel_id_list.append(channel.id)
            self.bot.star_config[ctx.guild.id]["blacklist"] = ",".join([str(c) for c in channel_id_list])
            await ctx.send(f"Addded {channel.mention} to the blacklist!")
        else:
            await ctx.send("That channel's already in the blacklist!")

    @blacklist.command()
    @commands.check(univ.proper_permissions)
    async def remove(self, ctx, channel: discord.TextChannel):
        channel_id_list = [int(c) for c in self.bot.star_config[ctx.guild.id]["blacklist"].split(",") if c != ""]

        if channel.id in channel_id_list:
            channel_id_list.remove(channel.id)
            self.bot.star_config[ctx.guild.id]["blacklist"] = ",".join([str(c) for c in channel_id_list])
            await ctx.send(f"Removed {channel.mention} from the blacklist!")
        else:
            await ctx.send("That channel's not in the blacklist!")

def setup(bot):
    bot.add_cog(BlacklistCMDs(bot))