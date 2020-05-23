from discord.ext import commands
import discord, datetime, importlib, asyncio

import star_utils.universals as univ

class OwnerCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(univ)

    async def msg_handler(self, ctx, msg_str):
        await ctx.send(msg_str)

        utcnow = datetime.datetime.utcnow()
        time_format = utcnow.strftime("%x %X UTC")

        await univ.msg_to_owner(ctx.bot, f"`{time_format}`: {msg_str}")

    @commands.command()
    @commands.is_owner()
    async def load_extension(self, ctx, extension):
        try:
            self.bot.load_extension(extension)
        except commands.ExtensionNotFound:
            await ctx.send(f"Extension '{extension}' not found!")
            return
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"Extension '{extension}' is already loaded!")
            return

        await self.msg_handler(ctx, f"Extension '{extension}' loaded!")

    @commands.command()
    @commands.is_owner()
    async def reload_extension(self, ctx, extension):
        try:
            self.bot.reload_extension(extension)
        except commands.ExtensionNotFound:
            await ctx.send(f"Extension '{extension}' not found!")
            return
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Extension '{extension}' is not loaded!")
            return

        await self.msg_handler(ctx, f"Extension '{extension}' reloaded!")

    @commands.command()
    @commands.is_owner()
    async def unload_extension(self, ctx, extension):
        try:
            self.bot.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Extension '{extension}' is not loaded!'")
            return

        await self.msg_handler(ctx, f"Extension '{extension}' unloaded!")

    @commands.command()
    @commands.is_owner()
    async def reload_all_extensions(self, ctx):
        for extension in self.bot.extensions.keys():
            self.bot.reload_extension(extension)

        await self.msg_handler(ctx, f"All extensions reloaded!")

    @commands.command()
    @commands.is_owner()
    async def reload_database(self, ctx):
        extensions = list(self.bot.extensions.keys())

        for extension in extensions:
            self.bot.unload_extension(extension)

        self.bot.init_load = True
        self.bot.starboard = {}
        self.bot.star_config = {}

        self.bot.load_extension("cogs.db_handler")
        while self.bot.star_config == {}:
            await asyncio.sleep(0.1)

        for extension in extension:
            if extension != "cogs.db_handler":
                self.bot.load_extension(extension)

        self.bot.init_load = False
        await self.msg_handler(ctx, f"Database reloaded!")

def setup(bot):
    bot.add_cog(OwnerCMDs(bot))