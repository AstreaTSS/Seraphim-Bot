#!/usr/bin/env python3.7
from discord.ext import commands
import discord, datetime, os
import importlib, asyncio

import common.utils as utils

class CogControl(commands.Cog, name="Cog Control", command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def msg_handler(self, ctx, msg_str):
        await ctx.send(msg_str)

        utcnow = datetime.datetime.utcnow()
        time_format = utcnow.strftime("%x %X UTC")

        await utils.msg_to_owner(ctx.bot, f"`{time_format}`: {msg_str}")

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
    async def unload_extension(self, ctx, extension):
        try:
            self.bot.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            return await ctx.send(f"Extension '{extension}' is not loaded!'")

        await self.msg_handler(ctx, f"Extension '{extension}' unloaded!")

    @commands.command(hidden=True)
    async def reload_all_extensions(self, ctx):
        extensions = [i for i in self.bot.extensions.keys() if i != "cogs.db_handler"]
        for extension in extensions:
            self.bot.reload_extension(extension)

        await self.msg_handler(ctx, f"All extensions reloaded!")

    @commands.command(hidden=True)
    async def refresh_extensions(self, ctx):
        def ext_str(list_files):
            exten_list = [f"`{k}`" for k in list_files]
            return ", ".join(exten_list)

        unloaded_files = []
        reloaded_files = []
        loaded_files = []
        not_loaded = []

        ext_files = utils.get_all_extensions(os.environ.get("DIRECTORY_OF_FILE"))

        to_unload = [e for e in self.bot.extensions.keys() 
        if e not in ext_files and e != "cogs.db_handler"]
        for ext in to_unload:
            self.bot.unload_extension(ext)
            unloaded_files.append(ext)
        
        for ext in ext_files:
            try:
                self.bot.reload_extension(ext)
                reloaded_files.append(ext)
            except commands.ExtensionNotLoaded:
                try:
                    self.bot.load_extension(ext)
                    loaded_files.append(ext)
                except commands.ExtensionNotFound as e:
                    await utils.error_handle(self.bot, e)
                except commands.NoEntryPointError:
                    not_loaded.append(ext)
                except commands.ExtensionFailed as e:
                    await utils.error_handle(self.bot, e)
            except commands.ExtensionNotFound as e:
                await utils.error_handle(self.bot, e)
            except commands.NoEntryPointError:
                not_loaded.append(ext)
            except commands.ExtensionFailed as e:
                await utils.error_handle(self.bot, e)

        msg_content = ""

        if unloaded_files != []:
            msg_content += f"Unloaded: {ext_str(unloaded_files)}\n"
        if loaded_files != []:
            msg_content += f"Loaded: {ext_str(loaded_files)}\n"
        if reloaded_files != []:
            msg_content += f"Reloaded: {ext_str(reloaded_files)}\n"
        if not_loaded != []:
            msg_content += f"Didn't load: {ext_str(not_loaded)}\n"
            
        await self.msg_handler(ctx, msg_content)

    @commands.command(hidden=True)
    async def list_loaded_extensions(self, ctx):
        exten_list = [f"`{k}`" for k in self.bot.extensions.keys()]
        exten_str = ", ".join(exten_list)
        await ctx.send(f"Extensions: {exten_str}")

    @commands.command(hidden=True)
    async def reload_database(self, ctx):
        loc_split = __file__.split("cogs")
        start_path = loc_split[0]

        this_cog = utils.file_to_ext(__file__, start_path)
        
        extensions = [ex for ex in self.bot.extensions.keys() if ex != this_cog]

        for extension in extensions:
            self.bot.unload_extension(extension)

        self.bot.init_load = True
        self.bot.starboard = {}
        self.bot.config = {}

        self.bot.load_extension("cogs.db_handler")
        while self.bot.config == {}:
            await asyncio.sleep(0.1)

        for extension in extensions:
            if extension != "cogs.db_handler":
                self.bot.load_extension(extension)

        self.bot.init_load = False
        await self.msg_handler(ctx, f"Database reloaded!")

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(CogControl(bot))