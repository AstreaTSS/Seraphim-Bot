#!/usr/bin/env python3.6
from discord.ext import commands, tasks
import discord, datetime

class SnipeCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_cleanup.start()

    def cog_unload(self):
        self.auto_cleanup.cancel()

    def snipe_cleanup(self, type_of, past_type, chan_id):
        now = datetime.datetime.utcnow()
        one_minute = datetime.timedelta(minutes=1)
        one_minute_ago = now - one_minute

        if chan_id in self.bot.snipes[type_of]:
            snipes_copy = self.bot.snipes[type_of][chan_id].copy()
            for entry in snipes_copy:
                if entry[f"time_{past_type}"] < one_minute_ago:
                    self.bot.snipes[type_of][chan_id].remove(entry)

    @tasks.loop(minutes=5)
    async def auto_cleanup(self):
        now = datetime.datetime.utcnow()
        one_minute = datetime.timedelta(minutes=1)
        one_minute_ago = now - one_minute

        for chan_id in self.bot.snipes["deletes"].keys():
            for entry in self.bot.snipes["deletes"][chan_id].copy():
                if entry[f"time_deleted"] < one_minute_ago:
                    self.bot.snipes["deletes"][chan_id].remove(entry)

        for chan_id in self.bot.snipes["edits"].keys():
            for entry in self.bot.snipes["edits"][chan_id].copy():
                if entry[f"time_edited"] < one_minute_ago:
                    self.bot.snipes["edits"][chan_id].remove(entry)

    async def snipe_handle(self, ctx, msg_num, type_of, past_type):
        self.snipe_cleanup(type_of, past_type, ctx.channel.id)

        if msg_num == 0:
            await ctx.send("You can't snipe the 0th to last message no matter how hard you try.")
            return

        msg_num = abs(msg_num)

        if not ctx.channel.id in self.bot.snipes[type_of].keys():
            await ctx.send("There's nothing to snipe!")
            return

        try:
            sniped_msg = self.bot.snipes[type_of][ctx.channel.id][-msg_num]
        except IndexError:
            await ctx.send("There's nothing to snipe!")
            return

        author = f"{sniped_msg['author'].display_name} ({str(sniped_msg['author'])})"
        icon = str(sniped_msg['author'].avatar_url_as(format=None,static_format='jpg', size=128))

        send_embed = discord.Embed(colour=discord.Colour(0x4378fc), description=sniped_msg["content"], timestamp=sniped_msg["created_at"])
        send_embed.set_author(name=author, icon_url=icon)

        await ctx.send(embed = send_embed)
        

    @commands.command()
    async def snipe(self, ctx, msg_num = 1):
        """Allows you to get the last or the nth to last deleted message from the channel this command was used in.
        Any message that had been deleted over a minute ago will not be able to be sniped."""

        await self.snipe_handle(ctx, msg_num, "deletes", "deleted")

    @commands.command()
    async def editsnipe(self, ctx, msg_num = 1):
        """Allows you to get either the last or nth lasted edited message from the channel this command was used in.
        Any message that has been edited in over a minute will not be able to be sniped."""

        await self.snipe_handle(ctx, msg_num, "edits", "edited")

def setup(bot):
    bot.add_cog(SnipeCMDs(bot))