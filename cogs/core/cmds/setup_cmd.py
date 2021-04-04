#!/usr/bin/env python3.8
from discord.ext import commands
import discord, importlib

import common.utils as utils
import common.groups as groups
import common.classes as custom_classes

class SetupCMD(commands.Cog, name="Setup"):
    def __init__(self, bot):
        self.bot = bot

    @groups.group()
    @commands.check(utils.proper_permissions)
    async def setup(self, ctx):
        """The base command for using the setup commands. See the help for the subcommands for more info.
        Only people with Manage Server permissions or higher can use these commands.
        This command is in beta. It may be unstable."""
        
        if ctx.invoked_subcommand == None:
            await ctx.send_help(ctx.command)

    @setup.command(aliases=["sb"])
    @commands.check(utils.proper_permissions)
    async def starboard(self, ctx: commands.Context):
        """Allows you to set up the starboard for Seraphim in an easy-to-understand way.
        Only people with Manage Server permissions or higher can use these commands.
        This command is in beta. It may be unstable."""

        final_str = "".join((
            "The setup is done. If you wish to view more options for the starboard, I suggest ",
            f"looking at `{ctx.prefix}settings starboard` command."
        ))
        wizard = custom_classes.WizardManager(
            embed_title="Starboard Setup",
            timeout=120.0,
            final_text=final_str
        )

        question_str = "".join((
            "Starboard, the reason why this bot exists in the first place. If you're setting this up, ",
            "I assume you know what it is.\n\n",
            "First off: what channel do you want the starboard in? This must be a channel the bot can ",
            "see, send and delete message, and react in. It also must already exist. You can mention it, ",
            "say the channel name exactly as is, or put the ID of it."
        ))
        def set_chan(ctx, converted):
            ctx.bot.config.setattr(ctx.guild.id, starboard_id=converted.id)
        wizard.add_question(question_str, commands.TextChannelConverter().convert, set_chan)

        question_str = "".join((
            "Well that's done with. Now for a more tricky question: what do you want the star limit to be?\n",
            "The star limit is how many stars a message needs to be on the starboard. Sometimes, this is called ",
            "the 'required' amount, as it's the amount required to be on the starboard. Either or. Just type a number."
        ))
        def int_convert(ctx, content):
            return int(content)
        def set_limit(ctx, converted):
            ctx.bot.config.setattr(ctx.guild.id, star_limit=converted)
        wizard.add_question(question_str, int_convert, set_limit)

        question_str = "Final question: do you want to enable the starboard? A simple 'yes' or 'no' will do."
        def bool_convert(ctx, content):
            lowered = content.lower()
            if lowered in ('yes', 'y', 'true', 't', '1'):
                return True
            elif lowered in ('no', 'n', 'false', 'f', '0'):
                return False
            else:
                raise discord.InvalidArgument
        def set_toggle(ctx, converted):
            if converted:
                ctx.bot.config.setattr(ctx.guild.id, star_toggle=True)
        wizard.add_question(question_str, bool_convert, set_toggle)

        await wizard.run(ctx)

def setup(bot):
    importlib.reload(utils)
    importlib.reload(groups)
    importlib.reload(custom_classes)

    bot.add_cog(SetupCMD(bot))