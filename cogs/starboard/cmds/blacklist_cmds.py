from discord.ext import commands
import discord, importlib

import common.utils as utils

class BlacklistCMDs(commands.Cog, name = "Blacklist"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return self.bot.config[ctx.guild.id]["star_toggle"]

    @commands.group(aliases = ["star_bl", "starblacklist"])
    @commands.check(utils.proper_permissions)
    async def star_blacklist(self, ctx):
        """The base command for the star blacklist. See the subcommands for more info.
        Requires Manage Server permissions or higher. Running this with no arguments will run the list command."""

        if ctx.invoked_subcommand == None:
            list_cmd = self.bot.get_command("blacklist list")
            await ctx.invoke(list_cmd)

    @star_blacklist.command(name = "list")
    @commands.check(utils.proper_permissions)
    async def _list(self, ctx):
        """Returns a list of channels that have been blacklisted. Messages from channels that are blacklisted won’t be starred."""

        channel_id_list = self.bot.config[ctx.guild.id]["star_blacklist"]
        if channel_id_list != []:
            channel_mentions = []

            for channel_id in channel_id_list:
                channel = await self.bot.get_channel(channel_id)

                if channel != None:
                    channel_mentions.append(channel.mention)
                else:
                    del self.bot.config[ctx.guild.id]["star_blacklist"][channel_id]

            if channel_mentions != []:
                await ctx.send(f"Blacklisted channels: {', '.join(channel_mentions)}")
                return
                
        await ctx.send("There's no blacklisted channels for this guild!")

    @star_blacklist.command()
    @commands.check(utils.proper_permissions)
    async def add(self, ctx, channel: discord.TextChannel):
        """Adds the channel to the blacklist."""

        channel_id_list = self.bot.config[ctx.guild.id]["star_blacklist"]

        if not channel.id in channel_id_list:
            channel_id_list.append(channel.id)
            self.bot.config[ctx.guild.id]["blacklist"] = channel_id_list
            await ctx.send(f"Addded {channel.mention} to the blacklist!")
        else:
            await ctx.send("That channel's already in the blacklist!")

    @star_blacklist.command()
    @commands.check(utils.proper_permissions)
    async def remove(self, ctx, channel: discord.TextChannel):
        """Removed the channel from the blacklist."""

        channel_id_list = self.bot.config[ctx.guild.id]["star_blacklist"]

        if channel.id in channel_id_list:
            channel_id_list.remove(channel.id)
            self.bot.config[ctx.guild.id]["blacklist"] = channel_id_list
            await ctx.send(f"Removed {channel.mention} from the blacklist!")
        else:
            await ctx.send("That channel's not in the blacklist!")

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(BlacklistCMDs(bot))