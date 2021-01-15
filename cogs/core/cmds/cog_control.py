#!/usr/bin/env python3.7
from discord.ext import commands
import os, importlib, asyncio, collections

import common.utils as utils
import common.star_classes as star_classes

class CogControl(commands.Cog, name="Cog Control", command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(hidden=True)
    async def reload_all_extensions(self, ctx):
        extensions = [i for i in self.bot.extensions.keys() if i != "cogs.db_handler"]
        for extension in extensions:
            self.bot.reload_extension(extension)

        await ctx.reply("All extensions reloaded!")

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

        msg_content = collections.deque()

        if unloaded_files != []:
            msg_content.append(f"Unloaded: {ext_str(unloaded_files)}")
        if loaded_files != []:
            msg_content.append(f"Loaded: {ext_str(loaded_files)}")
        if reloaded_files != []:
            msg_content.append(f"Reloaded: {ext_str(reloaded_files)}")
        if not_loaded != []:
            msg_content.append(f"Didn't load: {ext_str(not_loaded)}")
            
        await ctx.reply("\n".join(msg_content))

    @commands.command(hidden=True)
    async def list_loaded_extensions(self, ctx):
        exten_list = [f"`{k}`" for k in self.bot.extensions.keys()]
        exten_str = ", ".join(exten_list)
        await ctx.reply(f"Extensions: {exten_str}")

    @commands.command(hidden=True)
    async def reload_database(self, ctx):
        loc_split = __file__.split("cogs")
        start_path = loc_split[0]

        this_cog = utils.file_to_ext(__file__, start_path)
        
        extensions = [ex for ex in self.bot.extensions.keys() if ex != this_cog]

        for extension in extensions:
            self.bot.unload_extension(extension)

        self.bot.init_load = True
        self.bot.starboard = star_classes.StarboardEntries()
        self.bot.config = {}

        self.bot.load_extension("cogs.db_handler")
        while self.bot.config == {}:
            await asyncio.sleep(0.1)

        for extension in extensions:
            if extension != "cogs.db_handler":
                self.bot.load_extension(extension)

        self.bot.init_load = False
        await ctx.reply(f"Database reloaded!")

def setup(bot):
    importlib.reload(utils)
    bot.add_cog(CogControl(bot))