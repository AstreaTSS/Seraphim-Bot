import discord, importlib, datetime
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash import SlashCommand
from discord_slash import SlashContext

import common.utils as utils

"""Just going to note that these are still going to be rather limited for now.
Slash commands still need a lot of work before I can rely on them."""

class SlashCMDS(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "slash"):
            # Creates new SlashCommand instance to bot if bot doesn't have.
            bot.slash = SlashCommand(bot, override_type=True)
        self.bot = bot
        self.bot.slash.get_cog_commands(self)

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    def snipe_cleanup(self, type_of, chan_id):
        now = datetime.datetime.utcnow()
        one_minute = datetime.timedelta(minutes=1)
        one_minute_ago = now - one_minute

        if chan_id in self.bot.snipes[type_of]:
            snipes_copy = self.bot.snipes[type_of][chan_id].copy()
            for entry in snipes_copy:
                if entry.time_modified < one_minute_ago:
                    self.bot.snipes[type_of][chan_id].remove(entry)

    async def snipe_handle(self, ctx, chan, msg_num, type_of):
        # probably a better way of doing this
        if not ctx.guild:
            await ctx.send("You have to run this command in a guild for this to work.")
            return

        chan = chan if isinstance(chan, discord.Channel) else discord.Object(chan)
        msg_num = abs(msg_num)

        self.snipe_cleanup(type_of, chan.id)

        if msg_num == 0:
            await ctx.send("You can't snipe the 0th to last message no matter how hard you try.", complete_hidden=True)
            return

        if not chan.id in self.bot.snipes[type_of].keys():
            await ctx.send("There's nothing to snipe!", complete_hidden=True)
            return

        try:
            sniped_entry = self.bot.snipes[type_of][chan.id][-msg_num]
        except IndexError:
            await ctx.send("There's nothing to snipe!", complete_hidden=True)
            return
        
        await ctx.reply(embed = sniped_entry.embed)

    @cog_ext.cog_slash(name="reverse", auto_convert={"content", "STRING"})
    async def reverse(self, ctx: SlashContext, content):
        """Reverses the content given."""
        await ctx.send(f"{content[::-1]}", complete_hidden=True)

    @cog_ext.cog_slash(name="snipe")
    async def snipe(self, ctx: SlashContext):
        """Allows you to get the last deleted message from the channel this was used in.
        Any message that had been deleted over a minute ago will not be able to be sniped."""
        await self.snipe_handle(ctx, ctx.channel, 1, "deletes")

    @cog_ext.cog_slash(name="editsnipe")
    async def editsnipe(self, ctx: SlashContext):
        """Allows you to get the last edited message from the channel this was used in.
        Any message that had been edited over a minute ago will not be able to be sniped."""
        await self.snipe_handle(ctx, ctx.channel, 1, "edits")

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(SlashCMDS(bot))