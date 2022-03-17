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


class JoinLeaveLog(commands.Cog, name="Leave Logging"):
    def __init__(self, bot):
        self.bot: utils.SeraphimBase = bot

    class CheckForNone(commands.Converter):
        async def convert(self, ctx: commands.Context, argument: str):
            if argument.lower() == "none":
                return EmptyChannel()
            raise commands.BadArgument("Not 'none'!")

    @commands.command(aliases=["leave_log"])
    @utils.proper_permissions()
    async def leave_logs(
        self,
        ctx: utils.SeraContextBase,
        chan: typing.Union[cclasses.ValidChannelConverter, CheckForNone],
    ):
        """Sets (or unsets) the leave logs.
        This logs, as well as tracking what you expect, also track the roles a user had.
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
                name=str(member),
                icon_url=utils.get_icon_url(member._user.display_avatar),
            )
            leave_embed.set_footer(
                text=str(self.bot.user),
                icon_url=utils.get_icon_url(member.guild.me.display_avatar),
            )

            await chan.send(embed=leave_embed)


async def setup(bot):
    importlib.reload(cclasses)
    importlib.reload(utils)

    await bot.add_cog(JoinLeaveLog(bot))
