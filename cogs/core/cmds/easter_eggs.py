#!/usr/bin/env python3.8
from discord.ext import commands


class EasterEggs(commands.Cog, name="Easter Egg", command_attrs=dict(hidden=True)):
    """Just a bunch of easter eggs since no one looks at the source code anyways."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["theme_song", "theme-song"])
    async def themesong(self, ctx):
        """So there's a song called Seraphim... yeah...
        SERAPHIM by Odyssey ft. Jessa"""
        await ctx.reply("https://www.youtube.com/watch?v=4wWYVzwtHGg")

    @commands.command()
    async def sonic(self, ctx):
        await ctx.reply("...ok I guess...")

    @commands.command()
    async def sonic49(self, ctx):
        await ctx.reply(
            "Yes, that's my owner, thanks very much for using this pointless command."
        )

    @commands.command()
    async def soup(self, ctx):
        """Image is from https://commons.wikimedia.org/wiki/File:Tomato_soup,_plant-based_(44040252791).jpg
        and is distributed under the Creative Commons Attribution 2.0 Generic license, which
        can be found here: https://creativecommons.org/licenses/by/2.0/"""
        await ctx.reply(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Tomato_soup%2C_plant-based_"
            + +"%2844040252791%29.jpg/1280px-Tomato_soup%2C_plant-based_%2844040252791%29.jpg"
        )

    @commands.command()
    async def gitty(self, ctx):
        """Gitty (a user, that's all you need to know) won a challenge that I did, so this is part of her reward."""
        await ctx.reply(
            "https://cdn.discordapp.com/attachments/741011094155296780/791382459186937886/hello.png"
        )


def setup(bot):
    bot.add_cog(EasterEggs(bot))
