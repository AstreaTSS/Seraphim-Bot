#!/usr/bin/env python3.7
from discord.ext import commands
import discord, datetime, importlib, asyncio
from pathlib import Path

import star_utils.universals as univ

class CogControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(univ)

    async def msg_handler(self, ctx, msg_str):
        await ctx.send(msg_str)

        utcnow = datetime.datetime.utcnow()
        time_format = utcnow.strftime("%x %X UTC")

        await univ.msg_to_owner(ctx.bot, f"`{time_format}`: {msg_str}")

    def reload_or_load_extension(self, ext):
        try:
            self.bot.reload_extension(ext)
        except commands.ExtensionNotLoaded:
            self.bot.load_extension(ext)


    @commands.command()
    @commands.is_owner()
    async def load_extension(self, ctx, extension):
        try:
            self.bot.load_extension(extension)
        except commands.ExtensionNotFound:
            return await ctx.send(f"Extension '{extension}' not found!")
        except commands.ExtensionAlreadyLoaded:
            return await ctx.send(f"Extension '{extension}' already loaded!")
        except commands.NoEntryPointError:
            return await ctx.send(f"There was no entry point for '{extension}'!")
        except commands.ExtensionFailed:
            raise

        await self.msg_handler(ctx, f"Extension '{extension}' loaded!")

    @commands.command()
    @commands.is_owner()
    async def reload_extension(self, ctx, extension):
        try:
            self.bot.reload_extension(extension)
        except commands.ExtensionNotFound:
            return await ctx.send(f"Extension '{extension}' not found!")
        except commands.ExtensionNotLoaded:
            return await ctx.send(f"Extension '{extension}' not loaded!")
        except commands.NoEntryPointError:
            return await ctx.send(f"There was no entry point for '{extension}'!")
        except commands.ExtensionFailed:
            raise

        await self.msg_handler(ctx, f"Extension '{extension}' reloaded!")

    @commands.command()
    @commands.is_owner()
    async def unload_extension(self, ctx, extension):
        try:
            self.bot.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            return await ctx.send(f"Extension '{extension}' is not loaded!'")

        await self.msg_handler(ctx, f"Extension '{extension}' unloaded!")

    @commands.command()
    @commands.is_owner()
    async def reload_all_extensions(self, ctx):
        for extension in self.bot.extensions.keys():
            self.bot.reload_extension(extension)

        await self.msg_handler(ctx, f"All extensions reloaded!")

    @commands.command()
    @commands.is_owner()
    async def refresh_extensions(self, ctx):
        ext_files = []
        loaded_files = []

        pathlist = Path("cogs").glob('**/*.py')
        for path in pathlist:
            str_path = str(path.as_posix())
            str_path = str_path.replace("/", ".")
            str_path = str_path.replace(".py", "")

            ext_files.append(str_path)
        
        for ext in ext_files:
            try:
                self.reload_or_load_extension(ext)
                loaded_files.append(ext)
            except commands.ExtensionNotFound:
                raise
            except commands.NoEntryPointError:
                pass
            except commands.ExtensionFailed:
                raise

        exten_list = [f"`{k}`" for k in loaded_files]
        exten_str = ", ".join(exten_list)
        await self.msg_handler(ctx, f"Refreshed: {exten_str}")

    @commands.command()
    @commands.is_owner()
    async def list_loaded_extensions(self, ctx):
        exten_list = [f"`{k}`" for k in self.bot.extensions.keys()]
        exten_str = ", ".join(exten_list)
        await ctx.send(f"Extensions: {exten_str}")

    @commands.command()
    @commands.is_owner()
    async def reload_database(self, ctx):
        extensions = [ex for ex in self.bot.extensions.keys() if ex != "cogs.cmds.owner.cog_control"]

        for extension in extensions:
            self.bot.unload_extension(extension)

        self.bot.init_load = True
        self.bot.starboard = {}
        self.bot.star_config = {}

        self.bot.load_extension("cogs.db_handler")
        while self.bot.star_config == {}:
            await asyncio.sleep(0.1)

        for extension in extensions:
            if extension != "cogs.db_handler":
                self.bot.load_extension(extension)

        self.bot.init_load = False
        await self.msg_handler(ctx, f"Database reloaded!")

def setup(bot):
    bot.add_cog(CogControl(bot))