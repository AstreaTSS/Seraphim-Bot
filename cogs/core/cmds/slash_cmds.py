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

    reverse_content_option = {
        "type": 3,
        "name": "content",
        "description": "The content of the message that you wish to reverse.",
        "required": True
    }
    @cog_ext.cog_slash(name="reverse", description="Reverses the content given.", options=[reverse_content_option])
    async def reverse(self, ctx: SlashContext, content):
        await ctx.send(content=f"{content[::-1]}", complete_hidden=True)

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
        if isinstance(ex, discord.NotFound) and ex.text == "Unknown interaction":
            if isinstance(ctx.author, (discord.Member, discord.User)):
                author_str = ctx.author.mention
            else:
                author_str = f"<@{ctx.author}>"
            await ctx.channel.send(f"{author_str}, the bot is a bit slow and so cannot do slash commands right now. Please wait a bit and try again.",delete_after=3)
        else:
            await utils.error_handle(self.bot, ex, ctx)

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(SlashCMDS(bot))
