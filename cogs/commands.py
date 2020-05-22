#!/usr/bin/env python3.7
from discord.ext import commands
import discord, datetime
import cogs.star_universals as star_univ

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        await ctx.send("There are a couple of commands:\n\n`s!channel <channel mention>` - sets the starboard channel.\n" +
        "`s!limit <limit - positive number>` - sets the minimum number of stars needed to appear on the starboard.\n" +
        "`s!blacklist <optional: list, add, remove>` - allows for control over the blacklist that prevents " +
        "messages from being starred in that channel. With no arguments or with `list`, the bot will just report " +
        "the blacklisted channels. `add` and `remove` *require a channel mention* and allows you to add or remove " +
        "a channel from the blacklist.\n\n"
        "`s!ping` - gets the ping of the bot. Not really something you need to use unless you're the bot maker.\n" +
        "`s!help` - displays this message.")

    @commands.command()
    async def ping(self, ctx):
        current_time = datetime.datetime.utcnow().timestamp()
        mes_time = ctx.message.created_at.timestamp()

        ping_discord = round((self.bot.latency * 1000), 2)
        ping_personal = round((current_time - mes_time) * 1000, 2)

        await ctx.send(f"Pong!\n`{ping_discord}` ms from discord.\n`{ping_personal}` ms personally (not accurate)")

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.command()
    async def top_starred(self, ctx):
        def by_stars(elem):
            return star_univ.get_num_stars(elem)

        guild_entries = [self.bot.starboard[k] for k in self.bot.starboard.keys() if self.bot.starboard[k]["guild_id"] == ctx.guild.id]
        if guild_entries != []:
            top_embed = discord.Embed(title=f"Top starred messages in {ctx.guild.name}", colour=discord.Colour(0xcfca76), timestamp=datetime.datetime.utcnow())
            top_embed.set_author(name="Sonic's Starboard", icon_url=f"{str(ctx.guild.me.avatar_url_as(format='jpg', size=128))}")
            top_embed.set_footer(text="As of")

            starboard_id = self.bot.star_config[ctx.guild.id]['starboard_id']

            guild_entries.sort(reverse=True, key=by_stars)

            for i in range(len(guild_entries)):
                if i > 9:
                    break

                entry = guild_entries[i]
                url = f"https://discordapp.com/channels/{ctx.guild.id}/{starboard_id}/{entry['ori_mes_id_bac']}"
                num_stars = star_univ.get_num_stars(entry)
                member = ctx.guild.get_member(entry["author_id"])
                author_str = f"{member.display_name} ({str(member)})" if member != None else f"User ID: {entry['author_id']}"

                top_embed.add_field(name=f"#{i+1}: {num_stars} ⭐ from {author_str}", value=f"[Message]({url})")

            await ctx.send(embed=top_embed)
        else:
            await ctx.send("There are no starboard entries for this server!")

def setup(bot):
    bot.add_cog(Commands(bot))