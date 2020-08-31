from discord.ext import commands
import discord, importlib, typing

import io, functools, math, os
from PIL import Image

import common.utils as utils
import common.classes as classes
import common.image_utils as image_utils

class HelperCMDs(commands.Cog, name = "Helper"):
    """A series of commands made for tasks that are usually difficult to do, especially on mobile."""
    def __init__(self, bot):
        self.bot = bot

    def pil_compress(self, image, ext, flags):
        pil_image = Image.open(image)
        compress_image = io.BytesIO()

        try:
            noshrink = "noshrink" in flags.keys()
            if not noshrink:
                width = pil_image.width
                height = pil_image.height

                if width > 1920 or height > 1920:
                    bigger = width if width > height else height
                    factor = math.ceil(bigger / 1920)
                    pil_image = pil_image.reduce(factor=factor)

            if ext == "jpeg":
                pil_image.save(compress_image, format=ext, quality=80, optimize=True)
            elif ext in ("gif", "png"):
                pil_image.save(compress_image, format=ext, optimize=True)
            elif ext == "webp":
                pil_image.save(compress_image, format=ext, quality=80)
            else:
                compress_image.close()
                raise commands.BadArgument("Invalid file type!")

            compress_image.seek(0, os.SEEK_SET)

            return compress_image
            
        except BaseException:
            compress_image.close()
            raise

    @commands.command()
    async def compress(self, ctx, url: typing.Optional[image_utils.URLToImage], *, flags: typing.Optional[classes.FlagsConverter] = {}):
        """Compresses down the image given.
        It must be an image of type GIF, JPG, PNG, or WEBP. It must also be under 8 MB.
        Image quality will take a hit, and the image will shrink down if it's too big (unless you specify to not shrink the image).
        Flags: --noshrink (to not shrink the image), --jpg (to make the files a jpg, which is more efficient in terms of file space)."""

        if url == None:
            if ctx.message.attachments:
                if ctx.message.attachments[0].proxy_url.endswith(self.bot.image_extensions):
                    url = ctx.message.attachments[0].proxy_url
                else:
                    raise commands.BadArgument("Attachment provided is not a valid image.")
            else:
                raise commands.BadArgument("No URL or image given!")

        assert url != None

        async with ctx.channel.typing():
            image_data = await image_utils.get_file_bytes(url, 8388608, equal_to=False) # 8 MiB
            ori_image = io.BytesIO(image_data)

            mimetype = discord.utils._get_mime_type_for_image(image_data)
            ext = mimetype.split("/")[1]

            jpg_flag = "jpg" in flags.keys()
            if not jpg_flag:
                jpg_flag = "jpeg" in flags.keys()

            if jpg_flag:
                ext = "jpeg"

            compress = functools.partial(self.pil_compress, ori_image, ext, flags)
            compress_image = await self.bot.loop.run_in_executor(None, compress)

            ori_image.close()

            com_img_file = discord.File(compress_image, f"image.{ext}")
            await ctx.send(file=com_img_file)

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
            if ctx.message.attachments:
                if ctx.message.attachments[0].proxy_url.endswith(self.bot.image_extensions):
                    url = ctx.message.attachments[0].proxy_url
                else:
                    raise commands.BadArgument("Attachment provided is not a valid image.")
            else:
                raise commands.BadArgument("No URL or image given!")

        assert url != None

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
    importlib.reload(classes)
    importlib.reload(image_utils)
    
    bot.add_cog(HelperCMDs(bot))