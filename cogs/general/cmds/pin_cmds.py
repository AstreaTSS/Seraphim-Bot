from discord.ext import commands
import discord, importlib

import bot_utils.universals as univ

class PinCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(univ)

    @commands.group()
    @commands.check(univ.proper_permissions)
    async def manage_pin(self, ctx):
        if ctx.invoked_subcommand == None:
            list_cmd = self.bot.get_command("pin list")
            await ctx.invoke(list_cmd)

    @manage_pin.command(aliases = ["list"])
    @commands.check(univ.proper_permissions)
    async def _list(self, ctx):
        if self.bot.config[ctx.guild.id]["pin_config"] == {}:
            await ctx.send("There are no entries for this server!")
            return

        entries_list = []

        for entry in self.bot.config[ctx.guild.id]["pin_config"].keys():
            try:
                entry_chan = await self.bot.fetch_channel(int(entry))
                des_chan = self.bot.fetch_channel(self.bot.config[ctx.guild.id]["pin_config"][entry]["destination"])
                limit = self.bot.config[ctx.guild.id]["pin_config"][entry]["limit"]

                entries_list.append(f"{entry_chan.mention} -> {des_chan.mention} (Limit: {limit})")
            except discord.NotFound:
                continue

        entries_str = "\n".join(entries_list)

        await ctx.send(f"Channels mapped:\n\n{entries_str}")

    @manage_pin.command(aliases = ["map"])
    @commands.check(univ.proper_permissions)
    async def _map(self, ctx, entry: discord.TextChannel, destination: discord.TextChannel, limit: int):
        self.bot.config[ctx.guild.id]["pin_config"][str(entry.id)] = {
            "destination": destination.id,
            "limit": limit
        }

        await ctx.send(f"Overflowing pins from {entry.mention} will now appear in {destination.mention}.")

    @manage_pin.command(aliases = ["pinlimit"])
    @commands.check(univ.proper_permissions)
    async def pin_limit(self, ctx, entry: discord.TextChannel, limit: int):
        self.bot.config[ctx.guild.id]["pin_config"][str(entry.id)]["limit"] = limit
        await ctx.send(f"The pin limit for {entry.mention} is now set to {limit}.")

    @manage_pin.command()
    @commands.check(univ.proper_permissions)
    async def unmap(self, ctx, entry: discord.TextChannel):
        try:
            del self.bot.config[ctx.guild.id]["pin_config"][str(entry.id)]
            await ctx.send(f"Unmapped {entry.mention}.")
        except KeyError:
            await ctx.send("This channel wasn't mapped in the first place!")

def setup(bot):
    bot.add_cog(PinCMDs(bot))