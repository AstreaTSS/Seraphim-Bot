#!/usr/bin/env python3.8
import collections
import datetime
import importlib
import random
import typing

import discord
from discord.ext import commands
from discord.ext import flags

import common.classes as custom_classes
import common.fuzzys as fuzzys
import common.groups as groups
import common.star_classes as star_classes
import common.star_mes_handler as star_mes
import common.star_utils as star_utils
import common.utils as utils


class StarCMDs(commands.Cog, name="Starboard"):
    """Commands for the starboard. See the settings command to set up the starboard."""

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    def get_star_rankings(self, custom_filter):
        user_star_dict = collections.Counter()

        guild_entries = self.bot.starboard.get_list(custom_filter)

        if not guild_entries:
            return None

        for entry in guild_entries:
            if entry.author_id in user_star_dict.keys():
                user_star_dict[entry.author_id] += len(entry.get_reactors())
            else:
                user_star_dict[entry.author_id] = len(entry.get_reactors())

        return user_star_dict.most_common(None)

    def get_user_placing(self, user_star_list, author_id):
        author_entry = discord.utils.find(lambda e: e[0] == author_id, user_star_list)
        if author_entry:
            author_index = user_star_list.index(author_entry)
            return f"position: #{author_index + 1} with {author_entry[1]} ⭐"
        else:
            return "position: N/A - no stars found!"

    async def cog_check(self, ctx):
        return self.bot.config.getattr(ctx.guild.id, "star_toggle")

    @groups.group(
        invoke_without_command=True, aliases=["starboard", "star"], ignore_extra=False
    )
    async def sb(self, ctx):
        """Base command for running starboard commands. Use the help command for this to get more info."""
        await ctx.send_help(ctx.command)

    @sb.command()
    @utils.proper_permissions()
    async def setup(self, ctx: commands.Context):
        """An alias for `setup starboard`. Use the help command for that for more information."""
        sb_setup_cmd: typing.Optional[commands.Command] = ctx.bot.get_command(
            "setup starboard"
        )
        if not sb_setup_cmd:
            raise utils.CustomCheckFailure(
                "I couldn't find the command `setup starboard`. This should never happen, so join the support server to report this."
            )

        try:
            await sb_setup_cmd.can_run(ctx)
        except commands.CommandError:
            raise commands.CheckFailure

        await ctx.invoke(sb_setup_cmd)

    @sb.command(aliases=["conf", "config"])
    @utils.proper_permissions()
    async def settings(self, ctx: commands.Context):
        """An alias for `settings starboard`. Use the help command for that for more information."""
        msg = ctx.message

        base_sb_cmd: typing.Optional[commands.Command] = ctx.bot.get_command("sb")
        if not base_sb_cmd:
            raise utils.CustomCheckFailure(
                "I was unable to do... something. Join the support server to report this - tell that it's about sb settings."
            )

        # a bit of a hack, but basically...
        # we replace any way this command could be represented with 'settings starboard'
        # thus ensuring the alias actually is executed correctly, hopefully
        sb_names = [base_sb_cmd.name] + list(base_sb_cmd.aliases)
        this_names = [ctx.command.name] + list(ctx.command.aliases)

        for sb_name in sb_names:
            for this_name in this_names:
                msg.content = msg.content.replace(
                    f"{sb_name} {this_name}", "settings starboard", 1
                )

        await self.bot.process_commands(msg)

    @flags.add_flag("-role", "--role", type=discord.Role)
    @flags.add_flag("-user", "--user", type=discord.Member)
    @flags.add_flag("-bots", "--bots", type=bool, default=True)
    @sb.command(cls=flags.FlagCommand, aliases=["msg_top", "msglb", "msg_lb"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def msgtop(self, ctx, **flags):
        """Allows you to view the top 10 starred messages on a server. Cooldown of once every 5 seconds per user.
        Flags: --user <user>: allows you to view the top starred messages by the user specified.
        --role <role>: allows you to view the top starred messages by users who have the role specified.
        --bots <true/false>: if bot messages will be on the leaderboard."""

        optional_member: typing.Optional[discord.Member] = flags["user"]
        optional_role: typing.Optional[discord.Role] = flags["role"]
        if optional_role:
            role_members = frozenset(r.id for r in optional_role.members)

        if optional_member and optional_member.bot and not flags["bots"]:
            raise commands.BadArgument(
                "You can't just specify a user who is a bot and then filter out bots."
            )
        if optional_member and optional_role and optional_member not in role_members:
            raise commands.BadArgument(
                "You can't just specify both a user and a role and have that user not have that role."
            )

        if optional_member:
            guild_entries = self.bot.starboard.get_list(
                lambda e: e.guild_id == ctx.guild.id
                and e.author_id == optional_member.id
            )
        elif optional_role:
            guild_entries = self.bot.starboard.get_list(
                lambda e: e.guild_id == ctx.guild.id and e.author_id in role_members
            )
        else:
            guild_entries = self.bot.starboard.get_list(
                lambda e: e.guild_id == ctx.guild.id
            )

        if not guild_entries:
            raise utils.CustomCheckFailure(
                "There are no starboard entries for this server, role, and/or for this user!"
            )

        if optional_member:
            top_embed = discord.Embed(
                title=f"Top starred messages in {ctx.guild.name} by {optional_member.display_name} ({str(optional_member)})",
                colour=discord.Colour(0xCFCA76),
                timestamp=datetime.datetime.utcnow(),
            )
        else:
            top_embed = discord.Embed(
                title=f"Top starred messages in {ctx.guild.name}",
                colour=discord.Colour(0xCFCA76),
                timestamp=datetime.datetime.utcnow(),
            )
        top_embed.set_author(
            name=f"{self.bot.user.name}",
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png', size=128))}",
        )
        top_embed.set_footer(text="As of")

        guild_entries.sort(reverse=True, key=lambda e: len(e.get_reactors()))

        actual_entry_count = 0
        for entry in guild_entries:
            if actual_entry_count > 9:
                break

            starboard_id = entry.starboard_id

            url = f"https://discordapp.com/channels/{ctx.guild.id}/{starboard_id}/{entry.star_var_id}"
            num_stars = len(entry.get_reactors())

            if optional_role:
                member = (
                    ctx.guild.get_member(entry.author_id)
                    if not optional_member
                    else optional_member
                )
            else:
                member = (
                    await utils.user_from_id(self.bot, ctx.guild, entry.author_id)
                    if not optional_member
                    else optional_member
                )

            if flags["bots"] or not member or not member.bot:
                author_str = (
                    f"{member.display_name} ({str(member)})"
                    if member
                    else f"User ID: {entry.author_id}"
                )

                top_embed.add_field(
                    name=f"#{actual_entry_count+1}: {num_stars} ⭐ from {author_str}",
                    value=f"[Message]({url})\n",
                    inline=False,
                )
                actual_entry_count += 1

        if top_embed.fields == discord.Embed.Empty:
            raise utils.CustomCheckFailure(
                "There are no non-bot starboard entries for this server/role!"
            )
        await ctx.reply(embed=top_embed)

    @flags.add_flag("-role", "--role", type=discord.Role)
    @flags.add_flag("-bots", "--bots", type=bool, default=True)
    @sb.command(cls=flags.FlagCommand, name="top", aliases=["leaderboard", "lb"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def top(self, ctx, **flags):
        """Allows you to view the top 10 people with the most stars on a server. Cooldown of once every 5 seconds per user.
        Flags: --role <role>: allows you to filter by the role specified, only counting those who have that role.
        --bots <true/false>: if bot messages will be on the leaderboard."""

        optional_role: typing.Optional[discord.Role] = flags["role"]
        if optional_role:
            role_members = frozenset(r.id for r in optional_role.members)
            user_star_list = self.get_star_rankings(
                lambda e: e.guild_id == ctx.guild.id and e.author_id in role_members
            )
        else:
            user_star_list = self.get_star_rankings(
                lambda e: e.guild_id == ctx.guild.id
            )

        if not user_star_list:
            raise utils.CustomCheckFailure(
                "There are no starboard entries for this server/role!"
            )

        top_embed = discord.Embed(
            title=f"Star Leaderboard for {ctx.guild.name}",
            colour=discord.Colour(0xCFCA76),
            timestamp=datetime.datetime.utcnow(),
        )
        top_embed.set_author(
            name=f"{self.bot.user.name}",
            icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png', size=128))}",
        )

        actual_entry_count = 0
        filtered_star_list = []

        for entry in user_star_list:
            if actual_entry_count > 9 and flags["bots"]:
                break

            member = await utils.user_from_id(self.bot, ctx.guild, entry[0])

            if flags["bots"] or not member or not member.bot:
                filtered_star_list.append(entry)

                if actual_entry_count < 10:
                    num_stars = entry[1]
                    author_str = (
                        f"{member.display_name} ({str(member)})"
                        if member != None
                        else f"User ID: {entry[0]}"
                    )

                    top_embed.add_field(
                        name=f"#{actual_entry_count+1}: {author_str}",
                        value=f"{num_stars} ⭐\n",
                        inline=False,
                    )
                    actual_entry_count += 1

        if top_embed.fields == discord.Embed.Empty:
            raise utils.CustomCheckFailure(
                "There are no non-bot starboard entries for this server!"
            )
        elif not flags["bots"] or optional_role:
            top_embed.set_footer(
                text=f"Your filtered {self.get_user_placing(filtered_star_list, ctx.author.id)}"
            )
        else:
            top_embed.set_footer(
                text=f"Your {self.get_user_placing(filtered_star_list, ctx.author.id)}"
            )
        await ctx.reply(embed=top_embed)

    @sb.command(aliases=["position", "place", "placing"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def pos(self, ctx, *, user: typing.Optional[fuzzys.FuzzyMemberConverter]):
        """Allows you to get either your or whoever you mentioned’s position in the star leaderboard (like the top command, but only for one person).
        The user can be mentioned, searched up by ID, or you can say their name and the bot will attempt to search for that person."""

        member = ctx.author if not user else user
        user_star_list = self.get_star_rankings(lambda e: e.guild_id == ctx.guild.id)

        if user_star_list:
            if user:
                placing = f"{member.display_name}'s {self.get_user_placing(user_star_list, member.id)}"
            else:
                placing = f"Your {self.get_user_placing(user_star_list, member.id)}"

            place_embed = discord.Embed(
                colour=discord.Colour(0xCFCA76),
                description=placing,
                timestamp=datetime.datetime.utcnow(),
            )
            place_embed.set_author(
                name=f"{self.bot.user.name}",
                icon_url=f"{str(ctx.guild.me.avatar_url_as(format=None,static_format='png',size=128))}",
            )
            place_embed.set_footer(text="Sent")

            await ctx.reply(embed=place_embed)
        else:
            raise utils.CustomCheckFailure(
                "There are no starboard entries for this server!"
            )

    @sb.command()
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def random(self, ctx):
        """Gets a random starboard entry from the server it's being run in.
        May not work 100% of the time, but it should be reliable enough."""

        valid_entries = self.bot.starboard.get_list(
            lambda e: e.guild_id == ctx.guild.id and e.star_var_id != None
        )

        if not valid_entries:
            raise utils.CustomCheckFailure(
                "There are no starboard entries for me to pick!"
            )

        random_entry = random.choice(valid_entries)
        starboard_id = random_entry.starboard_id

        starboard_chan = ctx.guild.get_channel(starboard_id)
        if starboard_chan is None:
            raise utils.CustomCheckFailure(
                "I couldn't find the starboard channel for the entry I picked."
            )

        try:
            star_mes = await starboard_chan.fetch_message(random_entry.star_var_id)
        except discord.HTTPException:
            ori_url = f"https://discordapp.com/channels/{ctx.guild.id}/{random_entry.ori_chan_id}/{random_entry.ori_mes_id}"
            raise utils.CustomCheckFailure(
                "I picked an entry, but I couldn't get the starboard message.\n"
                + f"This might be the message I was trying to get: {ori_url}"
            )

        star_content = star_mes.content
        star_embed = star_mes.embeds[0]

        star_embed.add_field(
            name="Starboard Variant", value=f"[Jump]({star_mes.jump_url})", inline=True,
        )

        await ctx.reply(star_content, embed=star_embed)

    @sb.command(aliases=["info", "information"])
    async def stats(
        self,
        ctx: commands.Context,
        msg: typing.Union[discord.Message, custom_classes.UsableIDConverter],
    ):
        """Gets the starboard stats for a message. The message must had at least one star at some point, but does not need to be on the starboard.
        The message either needs to be a message ID of a message in the guild the command is being run in,
        a {channel id}-{message id} format, or the message link itself.
        The message can either be the original message or the starboard variant message."""

        msg_id = msg.id if isinstance(msg, discord.Message) else msg
        starboard_entry: star_classes.StarboardEntry = self.bot.starboard.get(msg_id)

        if not starboard_entry or starboard_entry.guild_id != ctx.guild.id:
            raise commands.BadArgument(
                "This message does not have an entry here internally."
            )

        ori_url = f"https://discordapp.com/channels/{ctx.guild.id}/{starboard_entry.ori_chan_id}/{starboard_entry.ori_mes_id}"
        if starboard_entry.star_var_id:
            star_url = f"[Here!](https://discordapp.com/channels/{ctx.guild.id}/{starboard_entry.starboard_id}/{starboard_entry.star_var_id})"
        else:
            star_url = None

        star_embed = discord.Embed(
            colour=discord.Colour(0xCFCA76),
            title="Stats for message given:",
            timestamp=datetime.datetime.utcnow(),
        )
        star_embed.description = "\n".join(
            (
                f"**Original Message ID:** {starboard_entry.ori_mes_id}",
                f"**Original Channel:** <#{starboard_entry.ori_chan_id}>",
                f"**Original Author:** <@{starboard_entry.author_id}>",
                f"**Original Message Link:** [Here!]({ori_url})",
                "",
                f"**Total Stars:** {len(starboard_entry.get_reactors())}",
                f"**Stars on Original Message:** {len(starboard_entry.ori_reactors)}",
                f"**Stars on Starred Varient:** {len(starboard_entry.var_reactors)}",
                "",
                f"**Has Starboard Entry:** {bool(starboard_entry.star_var_id)}",
                f"**Starboard Message ID:** {starboard_entry.star_var_id}",
                f"**Starboard Channel:** {f'<#{starboard_entry.starboard_id}>' if starboard_entry.star_var_id else None}",
                f"**Starboard Message Link:** {star_url}",
                "",
                f"**Forced:** {starboard_entry.forced}",
                f"**Frozen:** {starboard_entry.frozen}",
                f"**Trashed:** {starboard_entry.trashed}",
            )
        )

        await ctx.reply(embed=star_embed)

    @sb.command()
    async def reactors(
        self,
        ctx: commands.Context,
        msg: typing.Union[discord.Message, custom_classes.UsableIDConverter],
    ):
        """Gets the first 50 star reactors for a message. The message must had at least one star at some point, but does not need to be on the starboard.
        The message either needs to be a message ID of a message in the guild the command is being run in,
        a {channel id}-{message id} format, or the message link itself.
        The message can either be the original message or the starboard variant message."""

        msg_id = msg.id if isinstance(msg, discord.Message) else msg
        starboard_entry: star_classes.StarboardEntry = self.bot.starboard.get(msg_id)

        if not starboard_entry or starboard_entry.guild_id != ctx.guild.id:
            raise commands.BadArgument(
                "This message does not have an entry here internally."
            )

        ori_reactors_list = [
            f"<@{reactor}>" for reactor in starboard_entry.ori_reactors
        ][:50]
        var_reactors_list = [
            f"<@{reactor}>" for reactor in starboard_entry.var_reactors
        ][:50]

        star_embed = discord.Embed(
            colour=discord.Colour(0xCFCA76),
            title="Reactors for message given:",
            timestamp=datetime.datetime.utcnow(),
        )
        star_embed.description = "\n".join(
            (
                f"**Original Message Reactors:** {', '.join(ori_reactors_list)}",
                f"**Starboard Message Reactors:** {', '.join(var_reactors_list)}",
            )
        )

        await ctx.reply(embed=star_embed)

    async def initial_get(
        self, ctx, msg, forced=False, do_not_create=False
    ) -> star_classes.StarboardEntry:
        if not ctx.bot.config.getattr(ctx.guild.id, "star_toggle"):
            raise utils.CustomCheckFailure(
                "Starboard is not turned on for this server!"
            )

        if isinstance(msg, int):
            if do_not_create:
                raise commands.BadArgument(
                    "The message must be in the channel the command is being run in."
                )
            msg_id = msg
        else:
            msg_id = msg.id

        starboard_entry = ctx.bot.starboard.get(msg_id)
        if not starboard_entry:
            if not do_not_create:
                author_id = star_utils.get_author_id(msg, ctx.bot)
                starboard_entry = star_classes.StarboardEntry.new_entry(
                    msg, author_id, None, forced=forced
                )
                ctx.bot.starboard.add(starboard_entry)

                await star_utils.sync_prev_reactors(
                    ctx.bot, author_id, starboard_entry, remove=False
                )
            else:
                raise commands.BadArgument(
                    "This message does not have an entry here internally."
                )

        return starboard_entry

    @sb.command()
    @utils.proper_permissions()
    async def force(self, ctx, msg: discord.Message):
        """Forces a message onto the starboard, regardless of how many stars it has.
        The message either needs to be a message ID of a message in the channel the command is being run in,
        a {channel id}-{message id} format, or the message link itself.
        This message cannot be taken off the starboard unless it is deleted from it manually.
        You must have Manage Server permissions or higher to run this command."""

        starboard_entry = await self.initial_get(ctx, msg, forced=True)

        if starboard_entry.star_var_id:
            raise commands.BadArgument("This message is already on the starboard!")

        starboard_entry.forced = True
        self.bot.starboard.update(starboard_entry)
        self.bot.star_queue.put_nowait((msg.channel.id, msg.id, msg.guild.id))
        await ctx.reply(
            "Done! Please wait a couple of seconds for the message to appear."
        )

    @sb.command()
    @utils.proper_permissions()
    async def freeze(self, ctx, msg: discord.Message):
        """Freezes a message's star count. It does not have to be starred.
        The message either needs to be a message ID of a message in the channel the command is being run in,
        a {channel id}-{message id} format, or the message link itself.
        You must have Manage Server permissions or higher to run this command."""

        starboard_entry = await self.initial_get(ctx, msg)
        starboard_entry.frozen = True
        starboard_entry.updated = False
        self.bot.starboard.update(starboard_entry)
        if starboard_entry.star_var_id:
            await star_utils.star_entry_refresh(self.bot, starboard_entry, ctx.guild.id)

        await ctx.reply("The message's star count has been frozen.")

    @sb.command()
    @utils.proper_permissions()
    async def trash(
        self, ctx, msg: typing.Union[discord.Message, custom_classes.UsableIDConverter]
    ):
        """Removes a message from the starboard and prevents it from being starred again until untrashed.
        The message needs to a message that is on the starboard. It can be either the original or the starred message.
        The message either needs to be a message ID of a message,
        a {channel id}-{message id} format, or the message link itself.
        You must have Manage Server permissions or higher to run this command."""

        starboard_entry = await self.initial_get(ctx, msg, do_not_create=True)

        if not starboard_entry.star_var_id:
            raise commands.BadArgument("That message is not on the starboard!")

        starboard_entry.trashed = True
        starboard_entry.var_reactors = set()
        starboard_entry.updated = False
        self.bot.starboard.update(starboard_entry)

        chan = self.bot.get_channel(starboard_entry.starboard_id)
        if chan:
            try:
                mes = await chan.fetch_message(starboard_entry.star_var_id)
                await mes.delete()
                self.bot.star_queue.remove_from_copy(
                    (
                        starboard_entry.ori_chan_id,
                        starboard_entry.ori_mes_id,
                        starboard_entry.guild_id,
                    )
                )
            except discord.HTTPException:
                pass
        await ctx.reply("The message has been trashed.")

    @sb.command()
    @utils.proper_permissions()
    async def unfreeze(
        self, ctx, msg: typing.Union[discord.Message, custom_classes.UsableIDConverter]
    ):
        """Unfreezes a message's star count. The message must have been frozen before.
        The message either needs to be a message ID of a message
        a {channel id}-{message id} format, or the message link itself.
        You must have Manage Server permissions or higher to run this command."""

        starboard_entry = await self.initial_get(ctx, msg, do_not_create=True)
        if not starboard_entry.frozen:
            raise commands.BadArgument("This message is not frozen.")

        starboard_entry.frozen = False
        starboard_entry.updated = False
        self.bot.starboard.update(starboard_entry)
        if starboard_entry.star_var_id:
            await star_utils.star_entry_refresh(self.bot, starboard_entry, ctx.guild.id)

        await ctx.reply("The message's star count has been unfrozen.")

    @sb.command()
    @utils.proper_permissions()
    async def untrash(
        self, ctx, msg: typing.Union[discord.Message, custom_classes.UsableIDConverter]
    ):
        """Untrashes a message, allowing it to be starred and put on the starboard. The message must have been trashed before.
        The message either needs to be a message ID of a message,
        a {channel id}-{message id} format, or the message link itself.
        You must have Manage Server permissions or higher to run this command."""

        starboard_entry = await self.initial_get(ctx, msg, do_not_create=True)
        if not starboard_entry.trashed:
            raise commands.BadArgument("This message is not trashed.")

        starboard_entry.trashed = False
        starboard_entry.updated = False
        self.bot.starboard.update(starboard_entry)

        await ctx.reply("The message has been untrashed.")

    @sb.command(aliases=["update"])
    @utils.proper_permissions()
    async def refresh(
        self, ctx, msg: typing.Union[discord.Message, custom_classes.UsableIDConverter]
    ):
        """Refreshes a starboard entry, using the internal generator to remake the starboard message.
        Useful if you want to use the new starboard message features or if you want to update the avatar.
        The original message must also still exist.
        The message either needs to be a message ID of a message,
        a {channel id}-{message id} format, or the message link itself.
        You must have Manage Server permissions or higher to run this command."""

        starboard_entry = await self.initial_get(ctx, msg, do_not_create=True)

        starboard_chan = self.bot.get_channel(starboard_entry.starboard_id)
        try:
            starboard_msg = await starboard_chan.fetch_message(
                starboard_entry.star_var_id
            )
        except discord.HTTPException or AttributeError:
            raise utils.CustomCheckFailure(
                "The starboard message cannot be found! Make sure the bot can see the channel."
            )

        ori_chan = self.bot.get_channel(starboard_entry.ori_chan_id)
        try:
            ori_msg = await ori_chan.fetch_message(starboard_entry.ori_mes_id)
        except discord.HTTPException or AttributeError:
            raise utils.CustomCheckFailure(
                "The original message cannot be found! Make sure the bot can see the channel."
            )

        new_embed = await star_mes.star_generate(self.bot, ori_msg)
        new_content = star_utils.generate_content_str(starboard_entry)

        await starboard_msg.edit(content=new_content, embed=new_embed)
        await ctx.reply(
            f"Updated! Check out {starboard_msg.jump_url} to see the updated message!"
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def debug_star_mes(self, ctx, msg: discord.Message):
        send_embed = await star_mes.star_generate(self.bot, msg)
        await ctx.reply(embed=send_embed)


def setup(bot):
    importlib.reload(star_utils)
    importlib.reload(star_mes)
    importlib.reload(utils)
    importlib.reload(fuzzys)
    importlib.reload(groups)
    importlib.reload(custom_classes)

    bot.add_cog(StarCMDs(bot))
