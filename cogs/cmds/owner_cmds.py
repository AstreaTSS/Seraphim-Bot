from discord.ext import commands
import discord

class OwnerCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        await ctx.send(f"Extension '{extension}' loaded!")

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

        await ctx.send(f"Extension '{extension}' reloaded!")

    @commands.command()
    @commands.is_owner()
    async def unload_extension(self, ctx, extension):
        try:
            self.bot.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Extension '{extension}' is not loaded!'")
            return

        await ctx.send(f"Extension '{extension}' unloaded!")

    @commands.command()
    @commands.is_owner()
    async def reload_all_extensions(self, ctx):
        for extension in self.bot.extensions.keys():
            self.bot.reload_extension(extension)

        await ctx.send(f"All extensions reloaded!")

def setup(bot):
    bot.add_cog(OwnerCMDs(bot))