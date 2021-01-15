import discord, importlib, datetime, random
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
            await ctx.send(content="You have to run this command in a guild for this to work.")
            return

        chan = chan if isinstance(chan, discord.TextChannel) else discord.Object(chan)
        msg_num = abs(msg_num)

        self.snipe_cleanup(type_of, chan.id)

        if msg_num == 0:
            await ctx.send(content="You can't snipe the 0th to last message no matter how hard you try.")
            return

        if not chan.id in self.bot.snipes[type_of].keys():
            await ctx.send(content="There's nothing to snipe!")
            return

        try:
            sniped_entry = self.bot.snipes[type_of][chan.id][-msg_num]
        except IndexError:
            await ctx.send(content="There's nothing to snipe!")
            return
        
        await ctx.send(embeds = [sniped_entry.embed])

    reverse_content_option = {
        "type": 3,
        "name": "content",
        "description": "The content of the message that you wish to reverse.",
        "required": True
    }
    @cog_ext.cog_slash(name="reverse", description="Reverses the content given.", options=[reverse_content_option])
    async def reverse(self, ctx: SlashContext, content):
        await ctx.send(content=f"{content[::-1]}", complete_hidden=True)

    snipe_desc = """Allows you to get the last deleted message from the channel this was used in."""
    @cog_ext.cog_slash(name="snipe", description=snipe_desc)
    async def snipe(self, ctx: SlashContext):
        await self.snipe_handle(ctx, ctx.channel, 1, "deletes")

    editsnipe_desc = """Allows you to get the last edited message from the channel this was used in."""
    @cog_ext.cog_slash(name="editsnipe", description=editsnipe_desc)
    async def editsnipe(self, ctx: SlashContext):
        await self.snipe_handle(ctx, ctx.channel, 1, "edits")

    user_option = {
        "type": 6,
        "name": "user",
        "description": "The user to kill.",
        "required": True
    }
    killcmd_desc = "Allows you to kill the user specified using the iconic Minecraft kill command messages."
    @cog_ext.cog_slash(name="kill", description=killcmd_desc, options=[user_option])
    async def kill(self, ctx: SlashContext, user):
        kill_msg = random.choice(self.bot.death_messages)

        if isinstance(user, (discord.Member, discord.User)):
            user_str = f"**{user.display_name}**"
        else:
            user_str = f"<@{user}>"


        if isinstance(ctx.author, (discord.Member, discord.User)):
            author_str = f"**{ctx.author.display_name}**"
        else:
            author_str = f"<@{ctx.author}>"

        kill_msg = kill_msg.replace("%1$s", user_str)
        kill_msg = kill_msg.replace("%2$s", author_str)
        kill_msg = kill_msg.replace("%3$s", "*Seraphim*")
        kill_msg = f"{kill_msg}."

        kill_embed = discord.Embed(
            colour = discord.Colour.red(),
            description = kill_msg
        )

        await ctx.send(embeds=[kill_embed])

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, ex):
        await utils.error_handle(self.bot, ex, ctx)

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(SlashCMDS(bot))
