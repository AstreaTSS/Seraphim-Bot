#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib, math

import bot_utils.universals as univ

class OnErrors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(univ)

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        try:
            raise
        except Exception as e:
            await univ.error_handle(self.bot, e)
            
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                await univ.error_handle(self.bot, error)
        elif isinstance(error, (commands.ConversionError, commands.UserInputError)):
            await ctx.send(error)
        elif isinstance(error, commands.CheckFailure):
            if ctx.guild != None:
                await ctx.send("You do not have the proper permissions to use that command.")
        elif isinstance(error, commands.CommandOnCooldown):
            time_to_wait = math.ceil(error.retry_after)
            await ctx.send(f"You're doing that command too fast! Try again after {time_to_wait} seconds.")
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            await univ.error_handle(self.bot, error)

def setup(bot):
    bot.add_cog(OnErrors(bot))