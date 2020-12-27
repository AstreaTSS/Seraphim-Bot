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
            await ctx.send(content="You have to run this command in a guild for this to work.", hidden=True)
            return

        chan = chan if isinstance(chan, discord.TextChannel) else discord.Object(chan)
        msg_num = abs(msg_num)

        self.snipe_cleanup(type_of, chan.id)

        if msg_num == 0:
            await ctx.send(content="You can't snipe the 0th to last message no matter how hard you try.", hidden=True)
            return

        if not chan.id in self.bot.snipes[type_of].keys():
            await ctx.send(content="There's nothing to snipe!", hidden=True)
            return

        try:
            sniped_entry = self.bot.snipes[type_of][chan.id][-msg_num]
        except IndexError:
            await ctx.send(content="There's nothing to snipe!", hidden=True)
            return
        
        await ctx.send(embeds = [sniped_entry.embed])

    content_option = {
        "type": 3,
        "name": "content",
        "description": "The content of the message that you wish to reverse.",
        "required": True
    }
    @cog_ext.cog_slash(name="reverse", description="Reverses the content given.", options=[content_option], guild_ids=[775912554928144384])
    async def reverse(self, ctx: SlashContext, content):
        await ctx.send(content=f"{content[::-1]}", hidden=True)

    snipe_desc = """Allows you to get the last deleted message from the channel this was used in."""
    @cog_ext.cog_slash(name="snipe", description=snipe_desc)
    async def snipe(self, ctx: SlashContext):
        await self.snipe_handle(ctx, ctx.channel, 1, "deletes")

    editsnipe_desc = """Allows you to get the last edited message from the channel this was used in."""
    @cog_ext.cog_slash(name="editsnipe", description=editsnipe_desc)
    async def editsnipe(self, ctx: SlashContext):
        await self.snipe_handle(ctx, ctx.channel, 1, "edits")

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, ex):
        await utils.error_handle(self.bot, ex, ctx)

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(SlashCMDS(bot))