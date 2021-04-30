import functools
import importlib
import io
import math
import os
import typing
from enum import Enum

import discord
import humanize
from discord.ext import commands
from discord.ext import flags
from PIL import Image

import common.image_utils as image_utils
import common.utils as utils


class ImageCMDs(commands.Cog, name="Image"):
    """A series of commands for manipulating images in certain ways."""

    def __init__(self, bot):
        self.bot = bot

    def get_size(self, image: io.BytesIO):
        old_pos = image.tell()
        image.seek(0, os.SEEK_END)
        size = image.tell()
        image.seek(old_pos, os.SEEK_SET)

        return size

    def pil_compress(self, image, ext, flags):
        try:
            pil_image = Image.open(image)
            compress_image = io.BytesIO()

            if (
                flags["ori_ext"] in ("gif", "webp")
                and ext not in ("gif", "webp")
                and pil_image.is_animated
            ):
                raise commands.BadArgument(
                    "Cannot convert an animated image to this file type!"
                )

            if flags["shrink"]:
                width = pil_image.width
                height = pil_image.height

                if width > 1920 or height > 1920:
                    bigger = width if width > height else height
                    factor = math.ceil(bigger / 1920)
                    pil_image = pil_image.reduce(factor=factor)

            if ext == "jpeg":
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                pil_image.save(
                    compress_image, format=ext, quality=flags["quality"], optimize=True
                )
            elif ext in ("gif", "png"):
                pil_image.save(compress_image, format=ext, optimize=True)
            elif ext == "webp":
                pil_image.save(
                    compress_image,
                    format=ext,
                    minimize_size=True,
                    quality=flags["quality"],
                )
            else:
                compress_image.close()
                raise commands.BadArgument("Invalid file type!")

            compress_image.seek(0, os.SEEK_SET)

            return compress_image

        except:
            compress_image.close()
            raise
        finally:
            pil_image.close()

    def pil_resize(
        self,
        image,
        ext,
        percent: typing.Optional[float],
        width: typing.Optional[int],
        height: typing.Optional[int],
        filter: int,
    ):
        resized_image = io.BytesIO()

        try:
            pil_image = Image.open(image)

            ori_width = pil_image.width
            ori_height = pil_image.height

            if percent:
                new_width = math.ceil(pil_image.width * (percent / 100))
                new_height = math.ceil(pil_image.height * (percent / 100))
            elif bool(width) ^ bool(height):
                if width:
                    new_width = width
                    percent = width / pil_image.width
                    new_height = math.ceil(pil_image.height * percent)
                else:
                    new_height = height
                    percent = height / pil_image.height
                    new_width = math.ceil(pil_image.width * percent)
            else:
                new_width = width
                new_height = height

            pil_image = pil_image.resize((new_width, new_height), filter)

            pil_image.save(resized_image, format=ext)
            resized_image.seek(0, os.SEEK_SET)

            return resized_image, ori_width, ori_height, new_width, new_height
        except:
            resized_image.close()
            raise
        finally:
            pil_image.close()

    class ImageFilters(Enum):
        # what Pillow should have done
        NEAREST = 0
        NONE = 0
        BOX = 4
        BILINEAR = 2
        LINEAR = 2
        HAMMING = 5
        BICUBIC = 3
        CUBIC = 3
        LANCZOS = 1
        ANTIALIAS = 1

    def str_to_filter(self, argument: str):
        try:
            return self.ImageFilters[argument.upper()].value
        except KeyError:
            raise commands.BadArgument(f"Invalid filter `{argument}` provided!")

    @flags.add_flag("-shrink", "--shrink", type=bool, default=True)
    @flags.add_flag("-format", "--format", type=str, default="default")
    @flags.add_flag("-quality", "--quality", default=70, type=int)
    @flags.command()
    async def compress(
        self, ctx, url: typing.Optional[image_utils.URLToImage], **flags
    ):
        """Compresses down the image given.
        It must be an image of type GIF, JPG, PNG, or WEBP. It must also be under 8 MB.
        Image quality will take a hit, and the image will shrink down if it's too big (unless you specify to not shrink the image).
        Flags --shrink <true/false> (specifies to shrink the image - it will by default)
        --format <format> (converts the image to the specified format, and it must be 'gif, jpg, png, or webp' \
        - the resulting image will be in the same format as the original by default)
        --quality <number> (specifies quality from 0-100, only works with JPG and WEBP files, default is 70)"""

        if flags["format"] == "default":
            img_format = "default"
        else:
            img_type_checker = image_utils.ImageTypeChecker
            img_format = await img_type_checker.convert(
                img_type_checker, ctx, flags["format"]
            )

        if not 0 <= flags["quality"] <= 100:
            raise commands.BadArgument("Quality must be a number between 0-100!")

        if not url:
            url = image_utils.image_from_ctx(ctx)

        async with ctx.channel.typing():
            image_data = await image_utils.get_file_bytes(
                url, 8388608, equal_to=False
            )  # 8 MiB

            try:
                ori_image = io.BytesIO(image_data)

                mimetype = discord.utils._get_mime_type_for_image(image_data)
                ext = mimetype.split("/")[1]
                flags["ori_ext"] = ext

                if img_format != "default":
                    ext = flags["format"]

                compress = functools.partial(self.pil_compress, ori_image, ext, flags)
                compress_image = await self.bot.loop.run_in_executor(None, compress)

                ori_size = self.get_size(ori_image)
                compressed_size = self.get_size(compress_image)

            finally:
                del image_data
                if ori_image:
                    ori_image.close()

            try:
                com_img_file = discord.File(compress_image, f"image.{ext}")

                content = (
                    f"Original Size: {humanize.naturalsize(ori_size, binary=True)}\n"
                    + f"Reduced Size: {humanize.naturalsize(compressed_size, binary=True)}\n"
                    + f"Size Saved: {round(((1 - (compressed_size / ori_size)) * 100), 2)}%"
                )
            except:
                compress_image.close()
                raise

            await ctx.reply(content=content, file=com_img_file)

    @flags.add_flag("-shrink", "--shrink", type=bool, default=False)
    @flags.add_flag("-quality", "--quality", default=80, type=int)
    @flags.command(aliases=["image_convert"])
    async def img_convert(
        self,
        ctx,
        url: typing.Optional[image_utils.URLToImage],
        img_type: image_utils.ImageTypeChecker,
        **flags,
    ):
        """Converts the given image into the specified image type.
        Both the image and the specified image type must be of type GIF, JP(E)G, PNG, or WEBP. The image must also be under 8 MB.
        Flags: --shrink <true/false> (specifies to shrink the image - it won't by default)
        --quality <number> (specifies quality from 0-100, only works with JPG and WEBP files, default is 80)"""

        if not 0 <= flags["quality"] <= 100:
            raise commands.BadArgument("Quality must be a number between 0-100!")

        if not url:
            url = image_utils.image_from_ctx(ctx)

        async with ctx.channel.typing():
            image_data = await image_utils.get_file_bytes(
                url, 8388608, equal_to=False
            )  # 8 MiB

            try:
                ori_image = io.BytesIO(image_data)

                mimetype = discord.utils._get_mime_type_for_image(image_data)
                flags["ori_ext"] = mimetype.split("/")[1]
                ext = img_type

                compress = functools.partial(self.pil_compress, ori_image, ext, flags)
                converted_image = await self.bot.loop.run_in_executor(None, compress)
            finally:
                del image_data
                if ori_image:
                    ori_image.close()

            try:
                convert_img_file = discord.File(converted_image, f"image.{ext}")
            except:
                converted_image.close()
                raise

            await ctx.reply(file=convert_img_file)

    @flags.add_flag("-percent", "--percent", type=float)
    @flags.add_flag("-width", "--width", type=int)
    @flags.add_flag("-height", "--height", type=int)
    @flags.add_flag("-filter", "--filter", type=str)
    @flags.command(aliases=["image_resize"])
    async def img_resize(
        self, ctx, url: typing.Optional[image_utils.URLToImage], **flags
    ):
        """Resizes the image as specified by the flags.
        The image must be of type GIF, JP(E)G, PNG, or WEBP. The image must also be under 8 MB.

        Required flags:
        --percent <percent> (specifies the percent to reduce it to - whole numbers with no %, like '50', please.)
        --width <width> (specifies the width to reduce it to - it must be a whole number and greater than 0.)
        --height <height> (specifies the height to reduce it to - it must be a whole number and greater than 0.)

        Optional flags:
        --filter <filter> (specifies which resampling filter to use while downsizing - see \
        https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filters for the filters and which \
        one is best for you. Default is Bicubic.)
        """

        if flags["filter"]:
            filter = self.str_to_filter(flags["filter"])
        else:
            filter = Image.BICUBIC

        if not url:
            url = image_utils.image_from_ctx(ctx)

        if not (flags["percent"] or flags["width"] or flags["height"]):
            raise commands.BadArgument("No resizing arguments passed!")

        if flags["percent"] and (flags["width"] or flags["height"]):
            raise commands.BadArgument(
                "You cannot have a percentage and a width/height at the same time!"
            )

        if flags["percent"] and not flags["percent"] > 0:
            raise commands.BadArgument("The percent must be greater than 0!")

        if flags["width"] and not flags["width"] > 0:
            raise commands.BadArgument("The width must be greater than 0!")

        if flags["height"] and not flags["height"] > 0:
            raise commands.BadArgument("The height must be greater than 0!")

        async with ctx.channel.typing():
            image_data = await image_utils.get_file_bytes(
                url, 8388608, equal_to=False
            )  # 8 MiB

            try:
                ori_image = io.BytesIO(image_data)

                mimetype = discord.utils._get_mime_type_for_image(image_data)
                ext = mimetype.split("/")[1]

                resize = functools.partial(
                    self.pil_resize,
                    ori_image,
                    ext,
                    flags["percent"],
                    flags["width"],
                    flags["height"],
                    filter,
                )

                (
                    resized_image,
                    ori_width,
                    ori_height,
                    new_width,
                    new_height,
                ) = await self.bot.loop.run_in_executor(None, resize)
                resize_size = self.get_size(resized_image)

                if resize_size > 8388608:
                    resized_image.close()
                    del resized_image
                    raise commands.BadArgument("Resulting image was over 8 MiB!")
            finally:
                del image_data
                if ori_image:
                    ori_image.close()

            try:
                resized_img_file = discord.File(resized_image, f"image.{ext}")

                content = (
                    f"Original Image Dimensions: {ori_width}x{ori_height}\n"
                    + f"New Image Dimensions: {new_width}x{new_height}\n"
                    + f"Resized To: {flags['percent'] or round(((new_width / ori_width) * 100), 2)}%\n"
                    + f"New Image Size: {humanize.naturalsize(resize_size, binary=True)}"
                )
            except:
                resized_image.close()
                raise

            await ctx.reply(content=content, file=resized_img_file)


def setup(bot):
    importlib.reload(utils)
    importlib.reload(image_utils)

    bot.add_cog(ImageCMDs(bot))
