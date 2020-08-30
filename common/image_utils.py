from discord.ext import commands
from discord.ext.commands.errors import BadArgument
import asyncio, aiohttp, os, re, humanize

async def type_from_url(url):
    # gets type of data from url
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None

            data = await resp.content.read(12)
            tup_data = tuple(data)

            # first 7 bytes of most pngs
            png_list = (0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
            if tup_data[:8] == png_list:
                return "png"

            # first 12 bytes of most jp(e)gs. EXIF is a bit wierd, and so some manipulating has to be done
            jfif_list = (0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01)
            exif_lists = ((0xFF, 0xD8, 0xFF, 0xE1), (0x45, 0x78, 0x69, 0x66, 0x00, 0x00))

            if tup_data == jfif_list or (tup_data[:4] == exif_lists[0] and tup_data[6:] == exif_lists[1]):
                return "jpg"

            # first 3 bytes of some jp(e)gs.
            weird_jpeg_list = (0xFF, 0xD8, 0xFF)
            if tup_data[0:3] == weird_jpeg_list:
                return "jpg"

            # copied from d.py's _get_mime_type_for_image
            if tup_data[0:3] == b'\xff\xd8\xff' or tup_data[6:10] in (b'JFIF', b'Exif'):
                return "jpg"

            # first 6 bytes of most gifs. last two can be different, so we have to handle that
            gif_lists = ((0x47, 0x49, 0x46, 0x38), ((0x37, 0x61), (0x39, 0x61)))
            if tup_data[:4] == gif_lists[0] and tup_data[4:6] in gif_lists[1]:
                return "gif"

            # first 12 bytes of most webps. middle four are file size, so we ignore that
            webp_lists = ((0x52, 0x49, 0x46, 0x46), (0x57, 0x45, 0x42, 0x50))
            if tup_data[:4] == webp_lists[0] and tup_data[8:] == webp_lists[1]:
                return "webp"

    return None

async def tenor_handle(url: str):
    # handles getting gifs from tenor links
    dash_split = url.split("-")

    params = {
        "ids": dash_split[-1],
        "key": os.environ.get("TENOR_KEY"),
        "media_filter": "minimal"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.tenor.com/v1/gifs", params=params) as resp:
            resp_json = await resp.json()

            try:
                gif_url = resp_json["results"][0]["media"][0]["gif"]["url"]
                return gif_url
            except KeyError:
                return None
            except IndexError:
                return None

async def get_image_url(url: str):
    # handles getting true image url from a url

    image_endings = ("jpg", "jpeg", "png", "gif", "webp")
    image_extensions = tuple(image_endings) # no idea why I have to do this

    if "https://tenor.com/view" in url or "http://tenor.com/view" in url:
        gif_url = await tenor_handle(url)
        if gif_url != None:
            return gif_url
            
    else:
        file_type = await type_from_url(url)
        if file_type in image_extensions:
            return url

    return None

async def get_file_bytes(url: str, limit: int, equal_to = True):
    # gets a file as long as it's under the limit (in bytes)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                try:
                    if equal_to:
                        await resp.content.readexactly(limit + 1) # we want this to error out even if the file is exactly the limit
                        raise BadArgument(
                            f"The file/URL given is over {humanize.naturalsize(limit, binary=True)}!"
                        )
                    else:
                        await resp.content.readexactly(limit)
                        raise BadArgument(
                            f"The file/URL given is at or over {humanize.naturalsize(limit, binary=True)}!"
                        )

                except asyncio.IncompleteReadError as e:
                    # essentially, we're exploting the fact that readexactly will error out if
                    # the url given is less than the limit
                    return e.partial
            else:
                raise BadArgument("I can't get this file/URL!")

class URLToImage(commands.Converter):
    # gets either the URL or the image from an argument

    async def convert(self, ctx, argument):
        urls = re.findall(r"((\w+:\/\/)[-a-zA-Z0-9:@;?&=\/%\+\.\*!'\(\),\$_\{\}\^~\[\]`#|]+)", argument)
        if urls != []:
            first_url = urls[0][0]

            possible_url = await get_image_url(first_url)
            if possible_url != None:
                return possible_url
            else:
                raise BadArgument(f"Argument {argument} is not an image url.")