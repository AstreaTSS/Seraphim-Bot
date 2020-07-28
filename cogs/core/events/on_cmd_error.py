#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib
import datetime, humanize

import common.utils as utils

class OnCMDError(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
            
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                await utils.error_handle(self.bot, error, ctx)
        elif isinstance(error, (commands.ConversionError, commands.UserInputError, commands.BadArgument)):
            await ctx.send(error)
        elif isinstance(error, utils.CustomCheckFailure):
            await ctx.send(error)
        elif isinstance(error, commands.CheckFailure):
            if ctx.guild != None:
                await ctx.send("You do not have the proper permissions to use that command.")
        elif isinstance(error, commands.CommandOnCooldown):
            delta_wait = datetime.timedelta(seconds=error.retry_after)
            await ctx.send(f"You're doing that command too fast! Try again in {humanize.precisedelta(delta_wait, format='%0.0f')}.")
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            await utils.error_handle(self.bot, error, ctx)

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(OnCMDError(bot))