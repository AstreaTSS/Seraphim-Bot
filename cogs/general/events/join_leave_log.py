import importlib
import typing

import discord
from discord.ext import commands

import common.classes as cclasses
import common.utils as utils


class EmptyChannel:
    __slots__ = ("id", "mention")

    def __init__(self) -> None:
        self.id = None
        self.mention = None


class JoinLeaveLog(commands.Cog, name="Join and Leave Logging"):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    class CheckForNone(commands.Converter):
        async def convert(self, ctx: commands.Context, argument: str):
            if argument.lower() == "none":
                return EmptyChannel()
            raise commands.BadArgument("Not 'none'!")

    @commands.command()
    @utils.proper_permissions()
    async def join_leave_log(
        self,
        ctx: utils.SeraContextBase,
        chan: typing.Union[cclasses.ValidChannelConverter, CheckForNone],
    ):
        """Sets (or unsets) the join/leave logs.
        These logs, as well as tracking what you expect, also track roles and the invite used.
        Either specify a channel (mention/ID/name in quotes) to set it, or 'none' to unset it.
        The channel must be one the bot can send to.
        Requires Manage Server permissions or higher."""

        self.bot.config.setattr(ctx.guild.id, join_leave_chan_id=chan.id)
        await ctx.reply(f"Set the join/leave logging channel to {chan.mention}!")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if chan := member.guild.get_channel_or_thread(
            self.bot.config.getattr(member.guild.id, "join_leave_chan_id")
        ):
            role_names = ", ".join(
                tuple(r.name for r in member.roles if not r.is_default())
            )
            if not role_names:
                role_names = "None"

            leave_embed = discord.Embed(
                color=discord.Color.red(),
                description=f"{member} left",
                timestamp=discord.utils.utcnow(),
            )
            leave_embed.add_field(
                name="User Information",
                value=f"{member} ({member.id}) {member.mention}",
                inline=False,
            )
            leave_embed.add_field(name="Roles", value=role_names, inline=False)
            if member.joined_at:
                leave_embed.add_field(
                    name="Joined At",
                    value=(
                        f"{discord.utils.format_dt(member.joined_at, style='F')} ({discord.utils.format_dt(member.joined_at, 'R')})"
                    ),
                    inline=False,
                )
            leave_embed.add_field(
                name="Created At",
                value=(
                    f"{discord.utils.format_dt(member.created_at, style='F')} ({discord.utils.format_dt(member.created_at, 'R')})"
                ),
                inline=False,
            )
            leave_embed.add_field(
                name="ID", value=f"```ini\nUser = {member.id}\n```", inline=False
            )

            leave_embed.set_author(
                name=str(self.bot.user),
                icon_url=utils.get_icon_url(member.guild.me.display_avatar),
            )

            await chan.send(embed=leave_embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if chan := member.guild.get_channel_or_thread(
            self.bot.config.getattr(member.guild.id, "join_leave_chan_id")
        ):
            invite: typing.Optional[
                discord.Invite
            ] = await self.bot.tracker.fetch_inviter(member)

            join_embed = discord.Embed(
                color=discord.Color.green(),
                description=f"{member} joined",
                timestamp=discord.utils.utcnow(),
            )
            join_embed.add_field(
                name="User Information",
                value=f"{member} ({member.id}) {member.mention}",
                inline=False,
            )
            if member.joined_at:
                join_embed.add_field(
                    name="Joined At",
                    value=(
                        f"{discord.utils.format_dt(member.joined_at, style='F')} ({discord.utils.format_dt(member.joined_at, 'R')})"
                    ),
                    inline=False,
                )

            join_embed.add_field(name="Member Count", value=member.guild.member_count)
            if invite:
                join_embed.add_field(
                    name="Invite Used", value=f"{invite.code} with {invite.uses} uses"
                )
            join_embed.add_field(
                name="ID",
                value=f"```ini\nMember = {member.id}\nGuild = {member.guild.id}\n```",
                inline=False,
            )

            join_embed.set_author(
                name=str(self.bot.user),
                icon_url=utils.get_icon_url(member.guild.me.display_avatar),
            )

            await chan.send(embed=join_embed)


def setup(bot):
    importlib.reload(cclasses)
    importlib.reload(utils)

    bot.add_cog(JoinLeaveLog(bot))
