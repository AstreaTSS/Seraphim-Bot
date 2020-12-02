#!/usr/bin/env python3.7
import discord, os, asyncio
import websockets, logging
from discord.ext import commands
from discord.ext.commands.bot import _default as bot_default
from datetime import datetime

import common.star_classes as star_classes
import common.classes as custom_classes
import common.utils as utils

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(filename=os.environ.get("LOG_FILE_PATH"), level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s")

def seraphim_prefixes(bot: commands.Bot, msg: discord.Message):
    mention_prefixes = [f"{bot.user.mention} ", f"<@!{bot.user.id}> "]

    try:
        custom_prefixes = bot.config[msg.guild.id]["prefixes"]
    except AttributeError:
        # prefix handling runs before command checks, so there's a chance there's no guild
        custom_prefixes = ["s!"]
    except KeyError:
        # rare possibility, but you know
        custom_prefixes = []

    return mention_prefixes + custom_prefixes

def global_checks(ctx):
    if ctx.guild == None:
        return False

    if ctx.command == None:
        return True

    disable_entry = ctx.bot.config[ctx.guild.id]["disables"]["users"].get(str(ctx.author.id))
    if disable_entry == None:
        return True

    if ctx.command.qualified_name in disable_entry:
        return False

    if "all" in disable_entry and not ctx.command.cog.qualified_name in ("Cog Control", "Eval", "Help"):
        return False

    return True

class SeraphimBot(commands.Bot):
    def __init__(self, command_prefix, help_command=bot_default, description=None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)
        self._checks.append(global_checks)

    # methods for updating the custom cache, which is explained a bit more down below
    def get_members(self, guild_id: int):
        try:
            return list(self.custom_cache[guild_id].values)
        except KeyError:
            return None

    def update_member(self, member: discord.Member):
        try:
            self.custom_cache[member.guild.id][member.id] = member
        except KeyError:
            pass

    def remove_member(self, member: discord.Member):
        try:
            del self.custom_cache[member.guild.id][member.id]
        except KeyError:
            pass

    async def on_ready(self):
        if self.init_load == True:
            self.starboard = star_classes.StarboardEntries()
            self.config = {}

            self.star_queue = custom_classes.SetAsyncQueue()

            self.snipes = {
                "deletes": {},
                "edits": {}
            }
            self.role_rolebacks = {}

            image_endings = ("jpg", "jpeg", "png", "gif", "webp")
            self.image_extensions = tuple(image_endings) # no idea why I have to do this

            application = await self.application_info()
            self.owner = application.owner

            """Okay, let me explain myself here.
            Basically, on every disconnect, for some reason, discord.py decides to throw away
            every single member object it has if you don't have presences on.
            What I'm doing here is storing a copy of that member cache, and then giving it back
            to the bot after a disconnect. There's a better method, I know, but I don't have
            the experience to code something more advanced."""
            self.custom_cache = {}
            for guild in self.guilds:
                self.custom_cache[guild.id] = {}
                for member in guild.members:
                    self.update_member(member)

            self.load_extension("jishaku")
            self.load_extension("cogs.db_handler")
            while self.config == {}:
                await asyncio.sleep(0.1)

            cogs_list = utils.get_all_extensions(os.environ.get("DIRECTORY_OF_FILE"))

            for cog in cogs_list:
                if cog != "cogs.db_handler":
                    try:
                        self.load_extension(cog)
                    except commands.NoEntryPointError:
                        pass
        else:
            for guild in self.guilds:
                members = guild.members
                cache_members = self.get_members(guild.id)
                non_cache_members = [m for m in cache_members if not m in members]
                for non_cache_member in non_cache_members:
                    guild._add_member(non_cache_member) # dirty, but it has to be done

        utcnow = datetime.utcnow()
        time_format = utcnow.strftime("%x %X UTC")

        connect_msg = f"Logged in at `{time_format}`!" if self.init_load == True else f"Reconnected at `{time_format}`!"
        await self.owner.send(connect_msg)

        self.init_load = False

        activity = discord.Activity(name = 'over a couple of servers', type = discord.ActivityType.watching)

        try:
            await self.change_presence(activity = activity)
        except websockets.ConnectionClosedOK:
            await utils.msg_to_owner(self, "Reconnecting...")

    async def on_resumed(self):
        activity = discord.Activity(name = 'over a couple of servers', type = discord.ActivityType.watching)
        await self.change_presence(activity = activity)

    async def on_error(self, event, *args, **kwargs):
        try:
            raise
        except BaseException as e:
            await utils.error_handle(bot, e)

    async def get_context(self, message, *, cls=commands.Context):
        """A simple extension of get_content. If it doesn't manage to get a command, it changes the string used
        to get the command from - to _ and retries. Convenient for the end user."""

        ctx = await super().get_context(message, cls=cls)
        if ctx.command == None and ctx.invoked_with != None:
            ctx.command = self.all_commands.get(ctx.invoked_with.replace("-", "_"))

        return ctx

"""Suggesting the importance of which intents we use, let's break them down.
We need guilds as we need to know when the bot joins and leaves guilds for setup stuff. That's... mostly it.
We need members for their roles and nicknames. Yes, this stuff isn't provided normally.
Emojis are for the emoji helper commands, of course.
Messages run the entire core of the bot itself. Of course we use them here. We might be able to
turn off DM message intents, but for now they're here for safety.
Reactions run the starboard of Seraphim, so of course that's here too. See above for why DMs."""
intents = discord.Intents(guilds=True, members=True, 
    emojis=True, messages=True, reactions=True)

bot = SeraphimBot(command_prefix=seraphim_prefixes, chunk_guilds_at_startup=True, intents=intents)

bot.init_load = True
bot.run(os.environ.get("MAIN_TOKEN"))