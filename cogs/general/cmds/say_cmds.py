from discord.ext import commands
import discord, re, asyncio, importlib, typings

import common.utils as utils

class SayCMDS(commands.Cog, name = "Say"):
    def __init__(self, bot):
        self.bot = bot
        
    async def setup_helper(self, ctx, ori_mes, question, code_mes = True):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        if code_mes:
            await ori_mes.edit(
                content =  ("```\n" + question + 
                "\n\nYou have 10 minutes to reply to each question, otherwise this will automatically be exited." +
                "\nIf you wish to exit at any time, just say \"exit\".\n```")
            )
        else:
            await ori_mes.edit(
                content =  ("Due to Discord limitations, this question looks slightly different.\n\n" + question + 
                "\n\nYou have 10 minutes to reply to each question, otherwise this will automatically be exited." +
                "\nIf you wish to exit at any time, just say \"exit\".")
            )

        try:
            reply = await self.bot.wait_for('message', check=check, timeout=600.0)
        except asyncio.TimeoutError:
            await ori_mes.edit(content = "```\nFailed to reply. Exiting...\n```")
            return None
        else:
            if reply.content.lower() == "exit":
                await ori_mes.edit(content = "```\nExiting...\n```")
                return None
            else:
                return reply

    @commands.command()
    @commands.check(utils.proper_permissions)
    async def say(self, ctx, optional_channel: typings.Optional[discord.TextChannel], *, message):
        """Allows people with Manage Server permissions to speak with the bot. You can provide a channel and upload any attachments you wish to use."""

        args = message.split(" ")
        files_sent = []
            
        if ctx.message.attachments is not None:
            for a_file in ctx.message.attachments:
                to_file = await a_file.to_file()
                files_sent.append(to_file)
                
        if files_sent == []:
            if optional_channel is not None:
                await optional_channel.send(" ".join(args))
                await ctx.send(f"Done! Check out {optional_channel.mention}!")
            else:
                await ctx.send(" ".join(args))
        else:
            if optional_channel is not None:
                await optional_channel.send(content=" ".join(args), files=files_sent)
                await ctx.send(f"Done! Check out {optional_channel.mention}!")
            else:
                await ctx.send(content=" ".join(args), files=files_sent)
                
    @commands.command()
    @commands.check(utils.proper_permissions)
    async def embed_say(self, ctx):
        """Allows people with Manage Server permissions to speak with the bot with a fancy embed. Will open a wizard-like prompt."""
        
        optional_channel = None
        optional_color = None

        ori = await ctx.send("```\nSetting up...\n```")

        reply = await self.setup_helper(ctx, ori, (
            "Because of this command's complexity, this command requires a little wizard.\n\n" +
            "1. If you wish to do so, which channel do you want to send this message to? If you just want to send it in " +
            "this channel, just say \"skip\"."
        ))
        if reply == None:
            return
        elif reply.content.lower() != "skip":
            try:
                optional_channel = await commands.TextChannelConverter().convert(ctx, reply.content)
            except commands.BadArgument:
                await ori.edit(content = "```\nFailed to get channel. Exiting...\n```")
                return

        reply = await self.setup_helper(ctx, ori, (
            "2. If you wish to do so, what color, in hex (ex. #000000), would you like the embed to have. Case-insensitive, " +
            "does not require '#'.\nIf you just want the default color, say \"skip\"."
        ))
        if reply == None:
            return
        elif reply.content.lower() != "skip":
            try:
                optional_color = await commands.ColourConverter().convert(ctx, reply.content.lower())
            except commands.BadArgument:
                await ori.edit(content = "```\nFailed to get hex color. Exiting...\n```")
                return

        say_embed = discord.Embed()

        reply = await self.setup_helper(ctx, ori, (
            "3. What will be the title of the embed? Markdown (fancy discord editing) will work with titles."
        ))
        if reply == None:
            return
        else:
            say_embed.title = reply.content

        reply = await self.setup_helper(ctx, ori, (
            "4. What will be the content of the embed? Markdown (fancy discord editing) will work with content."
        ))
        if reply == None:
            return
        else:
            say_embed.description = reply.content

        if optional_color != None:
            say_embed.colour = optional_color

        if optional_channel != None:
            await optional_channel.send(embed = say_embed)
            await ctx.send(f"Done! Check out {optional_channel.mention}!")
        else:
            await ctx.send(embed = say_embed)

        await ori.edit(content = "```\nSetup complete.\n```")
        
def setup(bot):
    importlib.reload(utils)
    bot.add_cog(SayCMDS(bot))