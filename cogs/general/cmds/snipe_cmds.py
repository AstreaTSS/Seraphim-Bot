#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import discord, datetime

class SnipeCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipe_cleanup.start()

    def cog_unload(self):
        self.snipe_cleanup.cancel()

    #TODO: combine snipe and editsnipe into one function, but keep the seperate cmds

    @tasks.loop(minutes=5)
    async def snipe_cleanup(self):
        now = datetime.datetime.utcnow()
        one_minute = datetime.timedelta(minutes=1)
        one_minute_ago = now - one_minute

        for chan_id in self.bot.sniped.keys():
            for index in range(len(self.bot.sniped[chan_id])):
                if self.bot.sniped[chan_id][index]["time_deleted"] < one_minute_ago:
                    del self.bot.sniped[chan_id][index]

        for chan_id in self.bot.editsniped.keys():
            for index in range(len(self.bot.editsniped[chan_id])):
                if self.bot.editsniped[chan_id][index]["time_deleted"] < one_minute_ago:
                    del self.bot.editsniped[chan_id][index]

    @commands.command()
    async def snipe(self, ctx, msg_num = 1):
        """Allows you to get the last or the nth last deleted message from the channel this command was used in.
        Any message that had been deleted over a minute ago will not be able to be sniped."""

        no_msg_found = False
        msg_num = abs(msg_num)

        if not ctx.channel.id in self.bot.sniped.keys():
            no_msg_found = True
        else:
            now = datetime.datetime.utcnow()
            one_minute = datetime.timedelta(minutes=1)
            one_minute_ago = now - one_minute

            try:
                if self.bot.sniped[ctx.channel.id][-msg_num]["time_deleted"] < one_minute_ago:
                    no_msg_found = True
                    del self.bot.sniped[ctx.channel.id][-msg_num]
            except IndexError:
                no_msg_found = True

        if no_msg_found:
            await ctx.send("There's nothing to snipe!")
            return

        sniped_msg = self.bot.sniped[ctx.channel.id][-msg_num]

        author = f"{sniped_msg['author'].display_name} ({str(sniped_msg['author'])})"
        icon = str(sniped_msg['author'].avatar_url_as(format="jpg", size=128))

        send_embed = discord.Embed(colour=discord.Colour(0x4378fc), description=sniped_msg["content"], timestamp=sniped_msg["created_at"])
        send_embed.set_author(name=author, icon_url=icon)

        await ctx.send(embed = send_embed)

    @commands.command()
    async def editsnipe(self, ctx, msg_num = 1):
        """Allows you to get either the last or nth lasted edited message from the channel this command was used in.
        Any message that has been edited in over a minute will not be able to be sniped."""

        no_msg_found = False
        msg_num = abs(msg_num)

        if not ctx.channel.id in self.bot.editsniped.keys():
            no_msg_found = True
        else:
            now = datetime.datetime.utcnow()
            one_minute = datetime.timedelta(minutes=1)
            one_minute_ago = now - one_minute

            try:
                if self.bot.editsniped[ctx.channel.id][-msg_num]["time_edited"] < one_minute_ago:
                    no_msg_found = True
                    del self.bot.editsniped[-msg_num][ctx.channel.id]
            except IndexError:
                no_msg_found = True

        if no_msg_found:
            await ctx.send("There's nothing to snipe!")
            return

        sniped_msg = self.bot.editsniped[ctx.channel.id][-msg_num]

        author = f"{sniped_msg['author'].display_name} ({str(sniped_msg['author'])})"
        icon = str(sniped_msg['author'].avatar_url_as(format="jpg", size=128))

        send_embed = discord.Embed(colour=discord.Colour(0x4378fc), description=sniped_msg["content"], timestamp=sniped_msg["created_at"])
        send_embed.set_author(name=author, icon_url=icon)

        await ctx.send(embed = send_embed)

def setup(bot):
    bot.add_cog(SnipeCMDs(bot))