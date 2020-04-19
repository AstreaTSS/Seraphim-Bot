from discord.ext import commands
import discord
import cogs.interact_db as db

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        db.run_command(f"UPDATE starboard_config SET starboard_id = {channel.id} WHERE server_id = '{ctx.guild.id}")

        await ctx.send(f"Set channel to {channel.mention}!")

    @commands.command()
    async def limit(self, ctx, limit):
        if limit.isdigit():
            db.run_command(f"UPDATE starboard_config SET star_limit = {int(limit)} WHERE server_id = '{ctx.guild.id}")

            await ctx.send(f"Set limit to {limit}!")
        else:
            await ctx.send("That doesn't seem like a number to me...")

def setup(bot):
    bot.add_cog(Commands(bot))