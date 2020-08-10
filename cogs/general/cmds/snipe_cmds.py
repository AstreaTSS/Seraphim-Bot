#!/usr/bin/env python3.7
from discord.ext import commands, tasks
import discord, datetime, io, importlib, typing

import common.star_mes_handler as star_mes
import common.utils as utils

class SnipeCMDs(commands.Cog, name="Snipe"):
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

        for chan_id in list(self.bot.snipes["deletes"].keys()).copy():
            for entry in self.bot.snipes["deletes"][chan_id].copy():
                if entry[f"time_deleted"] < one_minute_ago:
                    self.bot.snipes["deletes"][chan_id].remove(entry)

        for chan_id in list(self.bot.snipes["edits"].keys()).copy():
            for entry in self.bot.snipes["edits"][chan_id].copy():
                if entry[f"time_edited"] < one_minute_ago:
                    self.bot.snipes["edits"][chan_id].remove(entry)

    @auto_cleanup.error
    async def error_handle(self, *args):
        error = args[-1]
        await utils.error_handle(self.bot, error)


    async def snipe_handle(self, ctx, chan, msg_num, type_of, past_type):
        chan = chan if chan != None else ctx.channel

        self.snipe_cleanup(type_of, past_type, chan.id)

        if msg_num == 0:
            raise commands.BadArgument("You can't snipe the 0th to last message no matter how hard you try.")

        msg_num = abs(msg_num)

        if not chan.id in self.bot.snipes[type_of].keys():
            raise commands.BadArgument("There's nothing to snipe!")


        try:
            sniped_msg = self.bot.snipes[type_of][chan.id][-msg_num]
        except IndexError:
            raise commands.BadArgument("There's nothing to snipe!")
            
        send_embed = discord.Embed(colour=discord.Colour(0x4378fc), description=sniped_msg["mes_content"], timestamp=sniped_msg["created_at"])
        send_embed.set_author(name=sniped_msg["author_name"], icon_url=sniped_msg["author_url"])
        send_embed.color = discord.Colour(0x4378fc)
        
        await ctx.send(embed = send_embed)


    @commands.command()
    async def snipe(self, ctx, chan: typing.Optional[discord.TextChannel], msg_num = 1):
        """Allows you to get the last or the nth to last deleted message from the channel mentioned or the channel this was used in.
        Any message that had been deleted over a minute ago will not be able to be sniped."""

        await self.snipe_handle(ctx, chan, msg_num, "deletes", "deleted")

    @commands.command()
    async def editsnipe(self, ctx, chan: typing.Optional[discord.TextChannel], msg_num = 1):
        """Allows you to get either the last or nth lasted edited message from the channel mentioned or the channel this was used in.
        Any message that has been edited in over a minute will not be able to be sniped."""

        await self.snipe_handle(ctx, chan, msg_num, "edits", "edited")

    @commands.command(aliases=["clearsnipe", "snipeclear"])
    @commands.check(utils.proper_permissions)
    async def clearsnipes(self, ctx, snipe_type, chan: typing.Optional[discord.TextChannel]):
        """Clears all snipes of the type specified from the bot, making them unable to be sniped. Useful for moderation.
        Type can be edits, deletes, or both. If no channel is specified, it assumes the current channel."""

        if chan == None:
            chan = ctx.channel

        lowered = snipe_type.lower()

        if lowered in ("edit", "edits", "edited", "editsnipe", "editsnipes"):
            self.bot.snipes["edits"][chan.id] = []
            await ctx.send(f"Cleared all edit snipes for {chan.mention}!")

        elif lowered in ("delete", "deleted", "deletes", "snipe", "snipes"):
            self.bot.snipes["deletes"][chan.id] = []
            await ctx.send(f"Cleared all deleted snipes for {chan.mention}!")

        elif lowered in ("both", "all"):
            self.bot.snipes["edits"][chan.id] = []
            self.bot.snipes["deletes"][chan.id] = []
            await ctx.send(f"Cleared all snipes for {chan.mention}!")

        else:
            raise commands.BadArgument("Incorrect snipe type!")

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(SnipeCMDs(bot))