import importlib
import io

import dateutil.parser
import discord
import orjson
from discord.ext import commands

import common.classes as custom_classes
import common.image_utils as image_utils
import common.utils as utils


class SayCMDS(commands.Cog, name="Say"):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    @commands.command()
    @utils.proper_permissions()
    @utils.bot_proper_perms()
    async def say(
        self,
        ctx: commands.Context,
        *,
        message: str,
    ):
        """Allows people with Manage Server permissions to speak with the bot.
        You can provide a channel and upload any attachments you wish to use."""

        first_argument = message.split(" ")[0]

        try:
            channel = await commands.TextChannelConverter().convert(ctx, first_argument)
        except commands.BadArgument:
            channel = ctx.channel

        rest_of_message = (
            message if channel == ctx.channel else " ".join(message.split(" ")[1:])
        )

        file_to_send = None
        file_io = None
        allowed_mentions = utils.generate_mentions(ctx)

        if ctx.message.attachments:
            if len(ctx.message.attachments) > 1:
                raise utils.CustomCheckFailure(
                    "I cannot say messages with more than one attachment due to"
                    " resource limits."
                )

            try:
                is_spoiler = ctx.message.attachments[0].is_spoiler()

                image_data = await image_utils.get_file_bytes(
                    ctx.message.attachments[0].url, 8388608, equal_to=False
                )  # 8 MiB
                file_io = io.BytesIO(image_data)
                file_to_send = discord.File(
                    file_io,
                    filename=ctx.message.attachments[0].filename,
                    spoiler=is_spoiler,
                )
            except:
                if file_io:
                    file_io.close()
                raise
            finally:
                del image_data

        if channel == ctx.channel:
            # girl manages to make files optional for the say command without doing
            # too much if statements! typehinters hate her!
            await ctx.send(
                content=rest_of_message,
                file=file_to_send,
                allowed_mentions=allowed_mentions,
            )

        else:
            await channel.send(
                content=rest_of_message,
                file=file_to_send,
                allowed_mentions=allowed_mentions,
            )
            await ctx.reply(f"Done! Check out {channel.mention}!")

    @commands.command()
    @utils.proper_permissions()
    @utils.bot_proper_perms()
    async def embed_say(self, ctx):
        """Allows people with Manage Server permissions to speak with the bot with a fancy embed. Will open a wizard-like prompt."""

        wizard = custom_classes.WizardManager(
            "Embed Say Wizard", "Setup complete.", pass_self=True
        )

        question_1 = (
            "Because of this command's complexity, this command requires a little"
            " wizard.\n\n"
            + "1. If you wish to do so, which channel do you want to send this message"
            " to? If you just want to send it in "
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
            "2. If you wish to do so, what color, in hex (ex. #000000), would you like"
            " the embed to have? Case-insensitive, "
            + "does not require '#'.\nIf you just want the default color, say \"skip\"."
        )

        async def color_convert(ctx, content):
            if content.lower() == "skip":
                return None
            if not content.startswith("#"):
                content = f"#{content}"
            return await commands.ColourConverter().convert(ctx, content.lower())

        def color_action(ctx, converted, self):
            self.optional_color = converted

        wizard.add_question(question_2, color_convert, color_action)

        question_3 = (
            "3. What will be the title of the embed? Markdown (fancy discord editing)"
            " will work with titles.\n"
            + "Make sure the title is less than or equal to 256 characters."
        )

        def title_convert(ctx, content):
            if len(content) > 256:
                raise commands.BadArgument("The title is too large!")
            return content

        def title_action(ctx, converted, self):
            self.say_embed = discord.Embed()
            self.say_embed.title = converted

        wizard.add_question(question_3, title_convert, title_action)

        question_4 = (
            "4. What will be the content of the embed? Markdown (fancy discord editing)"
            " will work with content."
        )

        def no_convert(ctx, content):
            return content

        async def final_action(ctx, converted, self):
            self.say_embed.description = converted

            if getattr(self, "optional_color", None):
                self.say_embed.color = self.optional_color

            if not getattr(self, "optional_channel", None):
                await ctx.send(embed=self.say_embed)
            else:
                await self.optional_channel.send(embed=self.say_embed)
                await ctx.reply(f"Done! Check out {self.optional_channel.mention}!")

        wizard.add_question(question_4, no_convert, final_action)

        await wizard.run(ctx)

    class RawEmbedSayConverter(commands.Converter):
        async def convert(self, ctx: commands.Context, argument: str):
            first_argument = argument.split(" ")[0]

            try:
                channel = await commands.TextChannelConverter().convert(
                    ctx, first_argument
                )
            except commands.BadArgument:
                channel = ctx.channel

            rest_of_argument = (
                argument
                if channel == ctx.channel
                else " ".join(argument.split(" ")[1:])
            )

            try:
                argument_json: dict = orjson.loads(rest_of_argument)

                if argument_json.get("timestamp"):
                    # python has a hard time with how some iso strings are
                    # dateutil should solve that problem, hopefully
                    try:
                        timestamp_date = dateutil.parser.isoparse(
                            argument_json["timestamp"]
                        )
                    except ValueError:
                        raise commands.BadArgument(
                            "The timestamp provided was not valid!"
                        )
                    argument_json["timestamp"] = timestamp_date.isoformat()
            except ValueError:
                raise commands.BadArgument(
                    "The argument provided was not valid embed JSON!"
                )

            try:
                return channel, discord.Embed.from_dict(argument_json)
            except ValueError:
                raise commands.BadArgument(
                    "Could not convert argument to an embed. Is it invalid?"
                )

    @commands.command()
    @utils.proper_permissions()
    async def raw_embed_say(
        self,
        ctx: commands.Context,
        *,
        data: RawEmbedSayConverter,
    ):
        """Allows people with Manage Server permissions to speak with the bot with a fancy embed with the JSON provided.
        This is a more low-level alternative to embed-say. If you know Discord Embed JSON, this allows you to use that.
        See https://discord.com/developers/docs/resources/channel#embed-object for the valid format.
        Do not use this if you have no idea what the above means. embed-say works fine.
        If you mention a channel before the embed data, the bot will send it to that channel."""

        chan: discord.TextChannel = data[0]
        embed: discord.Embed = data[1]

        if embed.to_dict() == {}:
            raise commands.BadArgument("The data provided is either invalid or empty!")
        elif not utils.embed_check(embed):
            raise commands.BadArgument(
                "The embed violates one or more of Discord's limits.\n"
                + "See https://discord.com/developers/docs/resources/channel#embed-limits"
                " for more information."
            )
        else:
            await chan.send(embed=embed)
            if chan != ctx.channel:
                await ctx.reply(f"Done! Check out {chan.mention}!")


def setup(bot):
    importlib.reload(custom_classes)
    importlib.reload(image_utils)
    importlib.reload(utils)
    bot.add_cog(SayCMDS(bot))
