from discord.ext import commands, tasks
import discord, aiohttp, os, asyncio

class UpdateConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fetch_document.start()

    @tasks.loop(minutes = 2)
    async def fetch_document(self):
        document_url = os.environ.get("CONFIG_URL")
        document = {}

        async with aiohttp.ClientSession() as session:
            async with session.get(document_url) as resp:
                document = await resp.json(content_type='text/plain')

        self.bot.config_file = document

def setup(bot):
    bot.add_cog(UpdateConfig(bot))