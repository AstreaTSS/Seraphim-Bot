from discord.ext import commands
import discord, datetime

async def proper_permissions(ctx):
    permissions = ctx.author.guild_permissions
    return (permissions.administrator or permissions.manage_messages)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(proper_permissions)
    async def channel(self, ctx, channel: discord.TextChannel):
        self.bot.star_config[ctx.guild.id]["starboard_id"] = channel.id
        await ctx.send(f"Set channel to {channel.mention}!")

    @commands.command()
    @commands.check(proper_permissions)
    async def limit(self, ctx, limit):
        if limit.isdigit():
            self.bot.star_config[ctx.guild.id]["star_limit"] = int(limit)
            await ctx.send(f"Set limit to {limit}!")
        else:
            await ctx.send("That doesn't seem like a valid number to me...")

    @commands.command()
    async def help(self, ctx):
        await ctx.send("There are four commands:\n\n`s?channel <channel mention>` - sets the starboard channel.\n" +
        "`s?limit <limit, positive number>` - sets the minimum number of stars needed to appear on the starboard.\n" +
        "`s?ping` - gets the ping of the bot. Not really something you need to use unless you're the bot maker.\n" +
        "`s?help` - displays this message.")

    @commands.command()
    async def ping(self, ctx):
        current_time = datetime.datetime.utcnow().timestamp()
        mes_time = ctx.message.created_at.timestamp()

        ping_discord = round((self.bot.latency * 1000), 2)
        ping_personal = round((current_time - mes_time) * 1000, 2)

        await ctx.send(f"Pong!\n`{ping_discord}` ms from discord.\n`{ping_personal}` ms personally (not accurate)")

def setup(bot):
    bot.add_cog(Commands(bot))