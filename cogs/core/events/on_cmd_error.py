#!/usr/bin/env python3.8
import datetime
import importlib

import discord
from discord.ext import commands

import common.utils as utils


class OnCMDError(commands.Cog):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: utils.SeraContextBase, error):
        # sourcery skip: remove-pass-elif
        if not ctx.bot.is_ready():
            return

        if isinstance(error, commands.CommandInvokeError):
            await utils.error_handle(self.bot, error, ctx)
        elif isinstance(error, commands.DisabledCommand):
            await ctx.reply(
                embed=utils.error_embed_generate(
                    (
                        f"{error}. This was most likely due to "
                        + "it being buggy or broken in some way - please wait for it to"
                        " be re-enabled."
                    )
                )
            )

        elif isinstance(error, commands.TooManyArguments):
            await ctx.reply(
                embed=utils.error_embed_generate(
                    "You passed too many arguments to that command! Please make sure"
                    " you're "
                    + "passing in a valid argument/subcommand."
                )
            )
        elif isinstance(error, commands.CommandOnCooldown):
            till = discord.utils.utcnow() + datetime.timedelta(
                seconds=error.retry_after
            )
            await ctx.reply(
                embed=utils.error_embed_generate(
                    "You're doing that command too fast! "
                    + f"Try again {discord.utils.format_dt(till, style='R')}."
                )
            )
        elif isinstance(
            error,
            (commands.ConversionError, commands.UserInputError, commands.BadArgument),
        ):
            await ctx.reply(embed=utils.error_embed_generate(str(error)))
        elif isinstance(error, (utils.CustomCheckFailure, utils.NotEnoughPerms)):
            await ctx.reply(embed=utils.error_embed_generate(str(error)))
        elif isinstance(error, commands.CheckFailure):
            if ctx.guild:
                await ctx.reply(
                    embed=utils.error_embed_generate(
                        "You do not have the proper permissions to use that command."
                    )
                )
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            await utils.error_handle(self.bot, error, ctx)


def setup(bot):
    importlib.reload(utils)
    bot.add_cog(OnCMDError(bot))
