#!/usr/bin/env python3.8
import datetime
import importlib
import typing

import discord
from discord.ext import commands
from discord.ext import tasks

import common.utils as utils


class SnipeCMDs(commands.Cog, name="Snipe"):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    async def cog_load(self):
        self.auto_cleanup.start()

    async def cog_unload(self):
        self.auto_cleanup.cancel()

    def snipe_cleanup(self, type_of, chan_id):
        now = discord.utils.utcnow()
        one_minute = datetime.timedelta(minutes=1)
        one_minute_ago = now - one_minute

        if chan_id in self.bot.snipes[type_of]:
            snipes_copy = self.bot.snipes[type_of][chan_id].copy()
            for entry in snipes_copy:
                if entry.time_modified < one_minute_ago:
                    self.bot.snipes[type_of][chan_id].remove(entry)

    @tasks.loop(minutes=5)
    async def auto_cleanup(self):
        now = discord.utils.utcnow()
        one_minute = datetime.timedelta(minutes=1)
        one_minute_ago = now - one_minute

        for chan_id in list(self.bot.snipes["deletes"].keys()).copy():
            for entry in self.bot.snipes["deletes"][chan_id].copy():
                if entry.time_modified < one_minute_ago:
                    self.bot.snipes["deletes"][chan_id].remove(entry)

        for chan_id in list(self.bot.snipes["edits"].keys()).copy():
            for entry in self.bot.snipes["edits"][chan_id].copy():
                if entry.time_modified < one_minute_ago:
                    self.bot.snipes["edits"][chan_id].remove(entry)

    @auto_cleanup.error
    async def error_handle(self, *args):
        error = args[-1]
        await utils.error_handle(self.bot, error)

    async def snipe_handle(self, ctx, chan, msg_num, type_of):
        chan = chan if chan != None else ctx.channel
        msg_num = abs(msg_num)

        self.snipe_cleanup(type_of, chan.id)

        if msg_num == 0:
            raise commands.BadArgument(
                "You can't snipe the 0th to last message no matter how hard you try."
            )

        if chan.id not in self.bot.snipes[type_of].keys():
            raise commands.BadArgument("There's nothing to snipe!")

        try:
            sniped_entry = self.bot.snipes[type_of][chan.id][-msg_num]
        except IndexError:
            raise commands.BadArgument("There's nothing to snipe!")

        await ctx.reply(embed=sniped_entry.embed)

    def clear_snipes(self, type_of, chan_id):
        if (
            chan_id not in self.bot.snipes[type_of]
            or self.bot.snipes[type_of][chan_id] == []
        ):
            raise commands.BadArgument("This channel doesn't have any snipes to clear!")

        self.bot.snipes[type_of][chan_id] = []

    @commands.command(aliases=["snipr"])
    async def snipe(self, ctx, chan: typing.Optional[discord.TextChannel], msg_num=1):
        """Allows you to get the last or the nth to last deleted message from the channel mentioned or the channel this was used in.
        Any message that had been deleted over a minute ago will not be able to be sniped.
        """

        await self.snipe_handle(ctx, chan, msg_num, "deletes")

    @commands.command(aliases=["editsnipr", "edit_snipe", "edit_snipr"])
    async def editsnipe(
        self, ctx, chan: typing.Optional[discord.TextChannel], msg_num=1
    ):
        """Allows you to get either the last or nth lasted edited message from the channel mentioned or the channel this was used in.
        Any message that has been edited in over a minute will not be able to be sniped.
        """

        await self.snipe_handle(ctx, chan, msg_num, "edits")

    @commands.command(aliases=["clearsnipe", "snipeclear", "cleansnipes"])
    @utils.proper_permissions()
    async def clearsnipes(
        self, ctx, snipe_type="both", chan: typing.Optional[discord.TextChannel] = None
    ):
        """Clears all snipes of the type specified from the bot (defaults to both types), making them unable to be sniped. Useful for moderation.
        Type can be edits, deletes, or both. If no channel is specified, it assumes the current channel.
        """

        if chan is None:
            chan = ctx.channel

        lowered = snipe_type.lower()

        if lowered in ("edit", "edits", "edited", "editsnipe", "editsnipes"):
            self.clear_snipes("edits", chan.id)
            await ctx.reply(f"Cleared all edit snipes for {chan.mention}!")

        elif lowered in ("delete", "deleted", "deletes", "snipe", "snipes"):
            self.bot.snipes["deletes"][chan.id] = []
            await ctx.reply(f"Cleared all deleted snipes for {chan.mention}!")

        elif lowered in ("both", "all"):
            error_count = 0  # we don't want it screaming at our faces if there's at least one valid snipe to clear

            try:
                self.clear_snipes("edits", chan.id)
            except commands.BadArgument:
                error_count += 1

            try:
                self.clear_snipes("deletes", chan.id)
            except commands.BadArgument:
                error_count += 1

            if error_count >= 2:
                raise commands.BadArgument(
                    "This channel doesn't have any snipes to clear!"
                )

            await ctx.reply(f"Cleared all snipes for {chan.mention}!")

        else:
            raise commands.BadArgument("Incorrect snipe type!")


async def setup(bot):
    importlib.reload(utils)
    await bot.add_cog(SnipeCMDs(bot))
