from discord.ext import commands, flags
import discord, importlib, typing, os

import common.utils as utils
import common.image_utils as image_utils

class HelperCMDs(commands.Cog, name = "Helper"):
    """A series of commands made for tasks that are usually difficult to do, especially on mobile."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["togglensfw"])
    @commands.check(utils.proper_permissions)
    async def toggle_nsfw(self, ctx, channel: typing.Optional[discord.TextChannel]):
        """Toggles either the provided channel or the channel the command is used it on or off NSFW mode.
        Useful for mobile devices, which for some reason cannot do this."""

        if channel == None:
            channel = ctx.channel

        toggle = not channel.is_nsfw()

        try:
            await channel.edit(nsfw = toggle)
            await ctx.send(f"{channel.mention} NSFW mode has been set to: {toggle}.")
        except discord.HTTPException as e:
            await ctx.send("".join(
                    ("I was unable to change this channel's NSFW mode! This might be due to me not having the ",
                    "permissions to or some other weird funkyness with Discord. Maybe this error will help you.\n",
                    f"Error: {e}")
                )
            )
            return

    @commands.command(aliases=["addemoji"])
    @commands.check(utils.proper_permissions)
    async def add_emoji(self, ctx, emoji_name, url: typing.Optional[image_utils.URLToImage]):
        """Adds the image or URL given as an emoji to this server.
        It must be an image of type GIF, JPG, or PNG. It must also be under 256 KB.
        The name must be at least 2 characters.
        Useful if you're on iOS and transparency gets the best of you or if you want to add an emoji from a URL."""

        if len(emoji_name) < 2:
            raise commands.BadArgument("Emoji name must at least 2 characters!")

        if url == None:
            url = image_utils.image_from_ctx(ctx)

        emoji_count = len(ctx.guild.emojis)
        if emoji_count >= ctx.guild.emoji_limit:
            raise utils.CustomCheckFailure("This guild has no more emoji slots!")

        async with ctx.channel.typing():
            emoji_data = await image_utils.get_file_bytes(url, 262144, equal_to=False) # 256 KiB, which I assume Discord uses

            try:
                emoji = await ctx.guild.create_custom_emoji(name=emoji_name, image=emoji_data, reason=f"Created by {str(ctx.author)}")
            except discord.HTTPException as e:
                await ctx.send("".join(
                        ("I was unable to add this emoji! This might be due to me not having the ",
                        "permissions or the name being improper in some way. Maybe this error will help you.\n",
                        f"Error: {e}")
                    )
                )
                return
            finally:
                del emoji_data

            await ctx.send(f"Added {str(emoji)}!")

    @commands.command(aliases=["getemojiurl"])
    async def get_emoji_url(self, ctx, emoji: typing.Union[discord.PartialEmoji, str]):
        """Gets the emoji URL from an emoji.
        The emoji does not have to be from the server it's used in, but it does have to be an emoji, not a name or URL."""

        if isinstance(emoji, str):
            raise commands.BadArgument("The argument provided is not a custom emoji!")

        if emoji.is_custom_emoji():
            await ctx.send(f"URL: {str(emoji.url)}")
        else:
            # this shouldn't happen due to how the PartialEmoji converter works, but you never know
            raise commands.BadArgument("This emoji is not a custom emoji!")

    @commands.command()
    @commands.check(utils.proper_permissions)
    async def publish(self, ctx, msg: discord.Message):
        """Publishes a message in a news channel. Useful if you're on mobile.
        The message either needs to be a message ID of a message in the channel the command is being run in,
        a {channel id}-{message id} format, or the message link itself.
        Both you and the bot need Manage Server permissions to use this."""

        if msg.channel.type != discord.ChannelType.news:
            raise commands.BadArgument("This channel isn't a news channel!")
        elif not msg.channel.permissions_for(ctx.guild.me).manage_messages:
            raise utils.CustomCheckFailure("I do not have the proper permissions to do that!")

        try:
            await msg.publish()
            await ctx.send("Published!")
        except discord.HTTPException as e:
            await ctx.send(f"An error occured. This shouldn't happen, but here's the error (it might be useful to you): {e}")

def setup(bot):
    importlib.reload(utils)
    importlib.reload(image_utils)
    
    bot.add_cog(HelperCMDs(bot))