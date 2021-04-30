import asyncio
import importlib
import io
import typing

import discord
from discord.ext import commands

import common.classes as custom_classes
import common.image_utils as image_utils
import common.utils as utils


class SayCMDS(commands.Cog, name="Say"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(utils.proper_permissions)
    async def say(
        self, ctx, optional_channel: typing.Optional[discord.TextChannel], *, message
    ):
        """Allows people with Manage Server permissions to speak with the bot. You can provide a channel and upload any attachments you wish to use."""

        args = message.split(" ")
        file_to_send = None
        file_io = None
        allowed_mentions = utils.generate_mentions(ctx)

        if ctx.message.attachments is not None and len(ctx.message.attachments) > 1:
            raise utils.CustomCheckFailure(
                "I cannot say messages with more than one attachment due to resource limits."
            )

        try:
            image_data = await image_utils.get_file_bytes(
                ctx.message.attachments[0].url, 8388608, equal_to=False
            )  # 8 MiB
            file_io = io.BytesIO(image_data)
            file_to_send = discord.File(
                file_io, filename=ctx.message.attachments[0].filename
            )
        except:
            if file_io:
                file_io.close()

        if file_to_send:
            if optional_channel is None:
                await ctx.send(" ".join(args), allowed_mentions=allowed_mentions)
            else:
                await optional_channel.send(
                    " ".join(args), allowed_mentions=allowed_mentions
                )
                await ctx.reply(f"Done! Check out {optional_channel.mention}!")
        else:
            if optional_channel is None:
                await ctx.send(
                    content=" ".join(args),
                    file=file_to_send,
                    allowed_mentions=allowed_mentions,
                )

            else:
                await optional_channel.send(
                    content=" ".join(args),
                    allowed_mentions=allowed_mentions,
                    file=file_to_send,
                )
                await ctx.reply(f"Done! Check out {optional_channel.mention}!")

    @commands.command()
    @commands.check(utils.proper_permissions)
    async def embed_say(self, ctx):
        """Allows people with Manage Server permissions to speak with the bot with a fancy embed. Will open a wizard-like prompt."""

        wizard = custom_classes.WizardManager(
            "Embed Say Wizard", 120, "Setup complete.", pass_self=True
        )

        question_1 = (
            "Because of this command's complexity, this command requires a little wizard.\n\n"
            + "1. If you wish to do so, which channel do you want to send this message to? If you just want to send it in "
            + 'this channel, just say "skip".'
        )

        async def chan_convert(ctx, content):
            if content.lower() == "skip":
                return None
            return await commands.TextChannelConverter().convert(ctx, content)

        def chan_action(ctx, converted, self):
            self.optional_channel = converted

        wizard.add_question(question_1, chan_convert, chan_action)

        question_2 = (
            "2. If you wish to do so, what color, in hex (ex. #000000), would you like the embed to have. Case-insensitive, "
            + "does not require '#'.\nIf you just want the default color, say \"skip\"."
        )

        async def color_convert(ctx, content):
            if content.lower() == "skip":
                return None
            return await commands.ColourConverter().convert(ctx, content.lower())

        def color_action(ctx, converted, self):
            self.optional_color = converted

        wizard.add_question(question_2, color_convert, color_action)

        question_3 = "3. What will be the title of the embed? Markdown (fancy discord editing) will work with titles."

        def no_convert(ctx, content):
            return content

        def title_action(ctx, converted, self):
            self.say_embed = discord.Embed()
            self.say_embed.title = converted

        wizard.add_question(question_3, no_convert, title_action)

        question_4 = "4. What will be the content of the embed? Markdown (fancy discord editing) will work with content."

        async def final_action(ctx, converted, self):
            self.say_embed.description = converted

            if getattr(self, "optional_color"):
                self.say_embed.color = self.optional_color

            if not getattr(self, "optional_channel"):
                await ctx.send(embed=self.say_embed)
            else:
                await self.optional_channel.send(embed=self.say_embed)
                await ctx.reply(f"Done! Check out {self.optional_channel.mention}!")

        wizard.add_question(question_4, no_convert, final_action)

        await wizard.run(ctx)


def setup(bot):
    importlib.reload(custom_classes)
    importlib.reload(image_utils)
    importlib.reload(utils)
    bot.add_cog(SayCMDS(bot))
