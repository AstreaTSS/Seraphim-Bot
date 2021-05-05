import datetime
import importlib
import io
import typing

import discord
from discord.ext import commands
from PIL import Image

import common.classes as custom_classes
import common.image_utils as image_utils
import common.utils as utils


class HelperCMDs(commands.Cog, name="Helper"):
    """A series of commands made for tasks that are usually difficult to do, especially on mobile."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["restoreroles"])
    @commands.check(utils.proper_permissions)
    async def restore_roles(self, ctx, member: discord.Member):
        """Restores the roles a user had before leaving, suggesting they left less than an hour ago.
        The user running this command must have Manage Server permissions.
        Useful for... accidential leaves? Troll leaves? Yeah, not much, but Despair's Horizon wanted it.
        Requires Manage Server permissions or higher."""

        guild_entry = self.bot.role_rolebacks.get(ctx.guild.id)
        if not guild_entry:
            raise commands.BadArgument(
                "That member did not leave in the last 15 minutes!"
            )

        member_entry = guild_entry.get(member.id)
        if member_entry == None:
            raise commands.BadArgument(
                "That member did not leave in the last 15 minutes!"
            )

        now = datetime.datetime.utcnow()
        hour_prior = now - datetime.timedelta(minutes=15)

        if member_entry["time"] < hour_prior:
            del self.bot.role_rolebacks[ctx.guild.id][member_entry["id"]]
            raise commands.BadArgument("That member did not leave in the last hour!")

        top_role = ctx.guild.me.top_role
        unadded_roles = []
        added_roles = []

        for role in member_entry["roles"]:
            if role.is_default():
                continue
            elif role > top_role or not role in ctx.guild.roles or role.managed:
                unadded_roles.append(role)
            elif role in member.roles:
                continue
            else:
                added_roles.append(role)

        if added_roles:
            try:
                await member.add_roles(
                    *added_roles,
                    reason=f"Restoring old roles: done by {str(ctx.author)}.",
                    atomic=False,
                )
            except discord.HTTPException as error:
                raise utils.CustomCheckFailure(
                    "Something happened while trying to restore the roles this user had.\n"
                    + "This shouldn't be happening, and this should have been caught earlier by the bot. Try contacting the bot owner about it.\n"
                    + f"Error: {error}"
                )
        else:
            raise commands.BadArgument("There were no roles to restore for this user!")

        del self.bot.role_rolebacks[ctx.guild.id][member_entry["id"]]

        final_msg = []
        final_msg.append(
            f"Roles restored: `{', '.join([r.name for r in added_roles])}`."
        )
        if unadded_roles:
            final_msg.append(
                f"Roles not restored: `{', '.join([r.name for r in unadded_roles])}`.\n"
                + "This was most likely because these roles are higher than the bot's own role, the roles no longer exist, "
                + "or the role is managed by Discord and so the bot cannot add it."
            )
        final_msg.append(
            "Please wait a bit for the roles to appear; sometimes Discord is a bit slow."
        )

        final_msg_str = "\n\n".join(final_msg)
        await ctx.reply(final_msg_str, allowed_mentions=utils.deny_mentions(ctx.author))

    @commands.command(aliases=["togglensfw"])
    @commands.check(utils.proper_permissions)
    async def toggle_nsfw(self, ctx, channel: typing.Optional[discord.TextChannel]):
        """Toggles either the provided channel or the channel the command is used it on or off NSFW mode.
        Useful for mobile devices, which for some reason cannot do this.
        Requires Manage Server permissions or higher."""

        if channel is None:
            channel = ctx.channel

        toggle = not channel.is_nsfw()

        try:
            await channel.edit(nsfw=toggle)
            await ctx.reply(
                f"{channel.mention}'s' NSFW mode has been set to: {toggle}."
            )
        except discord.HTTPException as e:
            raise utils.CustomCheckFailure(
                "".join(
                    (
                        "I was unable to change this channel's NSFW mode! This might be due to me not having the ",
                        "permissions to or some other weird funkyness with Discord. Maybe this error will help you.\n",
                        f"Error: {e}",
                    )
                )
            )

    @commands.command()
    @commands.check(utils.proper_permissions)
    async def suppress(self, ctx, msg: discord.Message):
        """Suppresses any embeds on the message, if there were any.
        Useful if you're a mobile user.
        Requires Manage Server permissions or higher."""
        if msg.flags.suppress_embeds:
            raise commands.BadArgument("This messages already has suppressed embeds!")

        try:
            await msg.edit(suppress=True)
            await ctx.reply("The message has successfully been suppressed.")
        except discord.HTTPException as e:
            raise utils.CustomCheckFailure(
                "".join(
                    (
                        "I was unable to suppress this message! This might be due to me not having the ",
                        "permissions to or some other weird funkyness with Discord. Maybe this error will help you.\n",
                        f"Error: {e}",
                    )
                )
            )

    @commands.command()
    @commands.check(utils.proper_permissions)
    async def unsuppress(self, ctx, msg: discord.Message):
        """Unsuppresses any embeds that were previously suppressed, if there were any.
        Yes, this is something bots can do, but for some reason, normal users can't.
        Requires Manage Server permissions or higher."""
        if not msg.flags.suppress_embeds:
            raise commands.BadArgument(
                "This message does not have any suppressed embeds!"
            )

        try:
            await msg.edit(suppress=False)
            await ctx.reply("The message has successfully been unsuppressed.")
        except discord.HTTPException as e:
            raise utils.CustomCheckFailure(
                "".join(
                    (
                        "I was unable to unsuppress this message! This might be due to me not having the ",
                        "permissions to or some other weird funkyness with Discord. Maybe this error will help you.\n",
                        f"Error: {e}",
                    )
                )
            )

    @commands.command(aliases=["addemoji"])
    @commands.check(utils.proper_permissions)
    async def add_emoji(
        self,
        ctx,
        emoji_name,
        emoji: typing.Union[image_utils.URLToImage, discord.PartialEmoji, None],
    ):
        """Adds the URL, emoji, or image given as an emoji to this server with the given name.
        If it's an URL or image, it must be of type GIF, JPG, or PNG. It must also be under 256 KB.
        If it's an emoji, it must not already be on the server the command is being used in.
        The name must be at least 2 characters.
        Useful if you're on iOS and transparency gets the best of you, you want to add an emoji from a URL, or
        you want to... take an emoji from another server.
        Requires Manage Server permissions or higher."""
        async with ctx.channel.typing():

            if len(emoji_name) < 2:
                raise commands.BadArgument("Emoji name must at least 2 characters!")

            if emoji is None:
                url = image_utils.image_from_ctx(ctx)
            elif isinstance(emoji, discord.PartialEmoji):
                possible_emoji = self.bot.get_emoji(emoji.id)
                if possible_emoji and possible_emoji.guild_id == ctx.guild.id:
                    raise commands.BadArgument("This emoji already exists here!")
                else:
                    url = str(emoji.url)
            else:
                url = emoji

            type_of = await image_utils.type_from_url(
                url
            )  # a bit redundent, but i dont see any other good way
            if type_of not in ("jpg", "jpeg", "png", "gif"):  # webp exists
                raise commands.BadArgument(
                    "This image's format is not valid for an emoji!"
                )

            animated = False
            emoji_data = None

            if type_of == "gif":  # you see, gifs can be animated or not animated
                # so we need to check for that via an admittedly risky operation

                emoji_data = await image_utils.get_file_bytes(
                    url, 262144, equal_to=False
                )  # 256 KiB, which I assume Discord uses

                raw_data = None
                emoji_image = None

                try:  # i think this operation is basic enough not to need a generator?
                    # not totally sure, though
                    raw_data = io.BytesIO(emoji_data)
                    emoji_image = Image.open(raw_data)
                    animated: bool = emoji_image.is_animated
                finally:
                    if raw_data:
                        raw_data.close()
                    if emoji_image:
                        emoji_image.close()

            else:
                animated = False

            if animated:
                emoji_count = len([e for e in ctx.guild.emojis if e.animated])
            else:
                emoji_count = len([e for e in ctx.guild.emojis if not e.animated])

            if emoji_count >= ctx.guild.emoji_limit:
                raise utils.CustomCheckFailure(
                    "This guild has no more emoji slots for that type of emoji!"
                )

            if not emoji_data:
                emoji_data = await image_utils.get_file_bytes(
                    url, 262144, equal_to=False
                )  # 256 KiB, which I assume Discord uses

            try:
                emoji = await ctx.guild.create_custom_emoji(
                    name=emoji_name,
                    image=emoji_data,
                    reason=f"Created by {str(ctx.author)}",
                )
            except discord.HTTPException as e:
                await ctx.reply(
                    "".join(
                        (
                            "I was unable to add this emoji! This might be due to me not having the ",
                            "permissions or the name being improper in some way. Maybe this error will help you.\n",
                            f"Error: {e}",
                        )
                    )
                )
                return
            finally:
                del emoji_data

            await ctx.reply(f"Added {str(emoji)}!")

    @commands.command(aliases=["copyemoji", "steal_emoji", "stealemoji"])
    @commands.check(utils.proper_permissions)
    async def copy_emoji(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        """Adds the emoji given to the server the command is run in, thus copying it.
        Useful if you have Discord Nitro and want to add some emojis from other servers into yours.
        This is essentially just the add-emoji command but if it only accepted an emoji and if it did not require you to put in a name.
        Thus, the same limitations as that command apply.
        Requires Manage Server permissions or higher."""

        add_emoji_cmd = self.bot.get_command("add_emoji")
        if not add_emoji_cmd:  # this should never happen
            raise utils.CustomCheckFailure(
                "For some reason, I cannot get the add-emoji command, which is needed for this. Join the support server to report this."
            )

        await ctx.invoke(add_emoji_cmd, emoji.name, emoji)

    @commands.command(aliases=["getemojiurl"])
    async def get_emoji_url(self, ctx, emoji: typing.Union[discord.PartialEmoji, str]):
        """Gets the emoji URL from an emoji.
        The emoji does not have to be from the server it's used in, but it does have to be an emoji, not a name or URL."""

        if isinstance(emoji, str):
            raise commands.BadArgument("The argument provided is not a custom emoji!")

        if emoji.is_custom_emoji():
            await ctx.reply(f"URL: {str(emoji.url)}")
        else:
            # this shouldn't happen due to how the PartialEmoji converter works, but you never know
            raise commands.BadArgument("This emoji is not a custom emoji!")

    @commands.command()
    async def created(
        # fmt: off
        self, ctx: commands.Context, *,
        # fmt: on
        argument: typing.Union[
            discord.Member,
            discord.User,
            discord.Message,
            discord.TextChannel,
            discord.VoiceChannel,
            discord.CategoryChannel,
            discord.Role,
            discord.PartialEmoji,
            custom_classes.UsableIDConverter,
        ],
    ):
        """Gets the creation date and time of many, MANY Discord related things, like members, emojis, messages, and much more.
        It would be too numberous to list what all can be converted (but usually, anything with a Discord ID will work) and how you input them.
        Names, IDs, mentions... try it out and see.
        Will return the time in UTC in MM/DD/YY HH:MM:SS in 24-hour time."""

        obj_id = argument.id if not isinstance(argument, int) else argument
        obj_creation = discord.utils.snowflake_time(obj_id)
        time_format = obj_creation.strftime("%x %X UTC")

        if isinstance(argument, discord.Role) and argument.is_default():
            # the @everyone role has the same id as the guild it's in
            # most people are probably looking for the guilds creation date, so...
            obj_name = f"`{discord.utils.escape_markdown(argument.guild.name)}`"
        elif isinstance(argument, (discord.Member, discord.User)):
            obj_name = f"`{discord.utils.escape_markdown(str(argument))}`"
        elif hasattr(argument, "name"):
            obj_name = f"`{discord.utils.escape_markdown(argument.name)}`"
        else:
            obj_name = "This"

        allowed_mentions = discord.AllowedMentions.none()
        allowed_mentions.replied_user = True

        await ctx.reply(
            f"{obj_name} was created at: `{time_format}` (MM/DD/YY HH:MM:SS)",
            allowed_mentions=allowed_mentions,
        )

    def quote_message(argument: str):
        return "\n".join(f"> {line}" for line in argument.splitlines())

    @commands.command(aliases=["spoil"])
    async def spoiler(
        self, ctx: commands.Context, *, message: typing.Optional[quote_message] = ""
    ):
        """Allows you to send a message that has a file marked as a spoiler.
        Just send the message you want to send along with the the file, and you'll be good to go.
        The file must be under 8 MiB. The actual text in the message itself will not be spoiled.
        Useful if you're on mobile, which for some reason, does not have the ability to mark a file as a spoiler."""

        file_to_send = None
        file_io = None
        allowed_mentions = utils.generate_mentions(ctx)

        if not ctx.message.attachments:
            raise commands.BadArgument("There's no attachment to mark as a spoiler!")
        elif len(ctx.message.attachments) > 1:
            raise utils.CustomCheckFailure(
                "I cannot spoil more than one attachment due to resource limits!"
            )
        elif len(message) > 1975:
            raise commands.BadArgument("This message is too long for me to send!")

        async with ctx.channel.typing():
            try:
                image_data = await image_utils.get_file_bytes(
                    ctx.message.attachments[0].url, 8388608, equal_to=False
                )  # 8 MiB
                await ctx.message.delete()

                file_io = io.BytesIO(image_data)
                file_to_send = discord.File(
                    file_io, filename=ctx.message.attachments[0].filename, spoiler=True,
                )
            except:
                if file_io:
                    file_io.close()
                raise
            finally:
                del image_data

            await ctx.send(
                f"From {ctx.author.mention}:\n{message}",
                file=file_to_send,
                allowed_mentions=allowed_mentions,
            )


def setup(bot):
    importlib.reload(utils)
    importlib.reload(image_utils)
    importlib.reload(custom_classes)

    bot.add_cog(HelperCMDs(bot))
