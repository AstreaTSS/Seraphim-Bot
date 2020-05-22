from discord.ext import commands
import discord

class OwnerCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return self.bot.is_owner(ctx.author)

    @commands.command()
    async def load_extension(self, ctx, extension):
        try:
            self.bot.load_extension(extension)
        except commands.ExtensionNotFound:
            await ctx.send(f"Extension '{extension}' not found!")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"Extension '{extension}' is already loaded!")

    @commands.command()
    async def reload_extension(self, ctx, extension):
        try:
            self.bot.reload_extension(extension)
        except commands.ExtensionNotFound:
            await ctx.send(f"Extension '{extension}' not found!")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Extension '{extension}' is not loaded!")

    @commands.command()
    async def unload_extension(self, ctx, extension):
        try:
            self.bot.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Extension '{extension}' is not loaded!'")

def setup(bot):
    bot.add_cog(OwnerCMDs(bot))