from discord.ext import commands
import discord, importlib

import bot_utils.universals as univ
import bot_utils.star_mes_handler as star_mes

class PinCMDs(commands.Cog, name = "Pinboard"):
    def __init__(self, bot):
        self.bot = bot

        importlib.reload(univ)
        importlib.reload(star_mes)

    @commands.group()
    @commands.check(univ.proper_permissions)
    async def manage_pinboard(self, ctx):
        """Base command for managing the pinboard. See the subcommands below. 
        Requires Manage Server permissions or higher. Running this command with no arguments will run list."""

        if ctx.invoked_subcommand == None:
            list_cmd = self.bot.get_command("manage_pinboard list")
            await ctx.invoke(list_cmd)

    @manage_pinboard.command(aliases = ["list"])
    @commands.check(univ.proper_permissions)
    async def _list(self, ctx):
        """Returns a list of channels that have their pins mapped to another channel, and the max limit before they overflow to that other channel."""

        if self.bot.config[ctx.guild.id]["pin_config"] == {}:
            await ctx.send("There are no entries for this server!")
            return

        entries_list = []

        for entry in self.bot.config[ctx.guild.id]["pin_config"].keys():
            try:
                entry_chan = await self.bot.fetch_channel(int(entry))
                des_chan = await self.bot.fetch_channel(self.bot.config[ctx.guild.id]["pin_config"][entry]["destination"])
                limit = self.bot.config[ctx.guild.id]["pin_config"][entry]["limit"]

                entries_list.append(f"{entry_chan.mention} -> {des_chan.mention} (Limit: {limit})")
            except discord.NotFound:
                continue

        entries_str = "\n".join(entries_list)

        await ctx.send(f"Channels mapped:\n\n{entries_str}")

    @manage_pinboard.command(aliases = ["map"])
    @commands.check(univ.proper_permissions)
    async def _map(self, ctx, entry: discord.TextChannel, destination: discord.TextChannel, limit: int):
        """Maps overflowing pins from the entry channel to go to the destination channel. 
        If there are more pins than the limit, it is considered overflowing."""

        self.bot.config[ctx.guild.id]["pin_config"][str(entry.id)] = {
            "destination": destination.id,
            "limit": limit
        }

        await ctx.send(f"Overflowing pins from {entry.mention} will now appear in {destination.mention}.")

    @manage_pinboard.command(aliases = ["pinlimit"])
    @commands.check(univ.proper_permissions)
    async def pin_limit(self, ctx, entry: discord.TextChannel, limit: int):
        """Changes the max limit of the entry channel to the provided limit."""

        self.bot.config[ctx.guild.id]["pin_config"][str(entry.id)]["limit"] = limit
        await ctx.send(f"The pin limit for {entry.mention} is now set to {limit}.")

    @manage_pinboard.command()
    @commands.check(univ.proper_permissions)
    async def unmap(self, ctx, entry: discord.TextChannel):
        """Umaps the entry channel, so overflowing pins do not get put into another channel."""

        try:
            del self.bot.config[ctx.guild.id]["pin_config"][str(entry.id)]
            await ctx.send(f"Unmapped {entry.mention}.")
        except KeyError:
            await ctx.send("This channel wasn't mapped in the first place!")

    @commands.command(aliases = ["pin_all"])
    @commands.check(univ.proper_permissions)
    async def pinall(self, ctx):
        """Retroactively moves overflowing pins from the channel this command is used in to the destination channel.
        Useful if you just mapped a channel and need to move old pin entries.
        Requires Manage Server permissions or higher."""

        if not str(ctx.channel.id) in self.bot.config[ctx.guild.id]["pin_config"].keys():
            await ctx.send("This channel isn't mapped!")
            return

        chan_entry = self.bot.config[ctx.guild.id]["pin_config"][str(ctx.channel.id)]

        pins = await ctx.channel.pins()

        if not len(pins) > chan_entry["limit"]:
            await ctx.send("The number of pins is below or at the limit!")
            return

        des_chan = self.bot.get_channel(chan_entry["destination"])
        if des_chan == None:
            await ctx.send("The destination channel doesn't exist anymore!")
            return

        dif = len(pins) - chan_entry["limit"]
        pins_subset = pins[-dif:]

        for pin in pins_subset:
            send_embed = await star_mes.generate(self.bot, pin)
            send_embed.color = discord.Colour.default()

            await des_chan.send(embed = send_embed)
            await pin.unpin()

        await ctx.send("Done!")

def setup(bot):
    bot.add_cog(PinCMDs(bot))