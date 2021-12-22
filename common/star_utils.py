#!/usr/bin/env python3.8
import discord
from discord.ext import commands

import common.star_classes as star_classes
import common.utils as utils


def get_reactor_type(mes_id: int, starboard_entry: star_classes.StarboardEntry):
    return (
        star_classes.ReactorType.ORI_REACTORS
        if mes_id == starboard_entry.ori_mes_id
        else star_classes.ReactorType.VAR_REACTORS
    )


def clear_stars(
    bot: utils.SeraphimBase, starboard_entry: star_classes.StarboardEntry, mes_id: int
):
    # clears entries from either ori or var reactors, depending on mes_id
    type_of = get_reactor_type(mes_id, starboard_entry)
    new_reactors = set()
    starboard_entry.set_reactors_of_type(type_of, new_reactors)

    bot.starboard.upsert(starboard_entry)


def get_star_emoji(num_stars: int):
    # TODO: make this customizable
    if num_stars <= 6:
        return "⭐"
    elif num_stars <= 12:
        return "🌟"
    elif num_stars <= 18:
        return "💫"
    else:
        return "✨"


def get_author_id(mes: discord.Message, bot: utils.SeraphimBase):
    # gets author id from message
    author_id = None
    if (
        mes.author.id == bot.user.id
        and mes.embeds != []
        and mes.embeds[0].author.name != discord.Embed.Empty
        and mes.embeds[0].author.name != bot.user.name
        and mes.embeds[0].type == "rich"
        and isinstance(mes.embeds[0].author.icon_url, str)
        and "&userid=" in mes.embeds[0].author.icon_url
    ):
        # conditions to check if message = sniped message from Seraphim
        # not perfect by any means, but it works for general use

        try:
            return int(mes.embeds[0].author.icon_url.split("&userid=")[1])
        except ValueError:
            return mes.author.id
    else:
        author_id = mes.author.id

    return author_id


def generate_content_str(entry: star_classes.StarboardEntry):
    unique_stars = len(entry.get_reactors())
    star_emoji = get_star_emoji(unique_stars)
    ori_chan_mention = f"<#{entry.ori_chan_id}>"

    modifiers = []
    if entry.forced:
        modifiers.append("forced")
    if entry.frozen:
        modifiers.append("frozen")

    if modifiers:
        return f"{star_emoji} **{unique_stars}** ({', '.join(modifiers)}) | {ori_chan_mention}"
    else:
        return f"{star_emoji} **{unique_stars}** | {ori_chan_mention}"


async def modify_stars(
    bot: utils.SeraphimBase, mes: discord.Message, reactor_id: int, operation
):
    # TODO: this method probably needs to be split up
    # modifies stars and creates an starboard entry if it doesn't exist already

    starboard_entry = await bot.starboard.get(mes.id)
    if not starboard_entry:
        author_id = get_author_id(mes, bot)
        starboard_entry = star_classes.StarboardEntry.new_entry(
            mes, author_id, reactor_id
        )
        bot.starboard.upsert(starboard_entry)

        await sync_prev_reactors(bot, author_id, starboard_entry, remove=False)

    author_id = starboard_entry.author_id

    if not starboard_entry.updated:
        # TODO: make it sync both reactors instead of only doing one
        type_of = get_reactor_type(mes.id, starboard_entry)
        await sync_prev_reactors(bot, author_id, starboard_entry)

        starboard_entry = await bot.starboard.get(starboard_entry.ori_mes_id)
        starboard_entry.updated = True

    if author_id != reactor_id:
        # this code probably needs slight rewriting
        type_of = get_reactor_type(mes.id, starboard_entry)

        if reactor_id not in starboard_entry.get_reactors() and operation == "ADD":
            starboard_entry.add_reactor(reactor_id, type_of)

        elif (
            operation == "SUBTRACT"
            and reactor_id in starboard_entry.get_reactors_from_type(type_of)
        ):
            starboard_entry.remove_reactor(reactor_id)

        bot.starboard.upsert(starboard_entry)

    elif bot.config.getattr(mes.guild.id, "remove_reaction"):
        # the previous if confirms this is the author who is reaction (simply by elimination), so...
        try:
            await mes.remove_reaction("⭐", mes.author)
        except discord.HTTPException:
            pass
        except discord.InvalidArgument:
            pass


async def sync_prev_reactors(
    bot: commands.Bot,
    author_id,
    starboard_entry: star_classes.StarboardEntry,
    remove=True,
):
    # syncs reactors stored in db with actual reactors on Discord

    async def sync_reactors(
        bot: utils.SeraphimBase,
        mes: discord.Message,
        starboard_entry: star_classes.StarboardEntry,
        type_of: star_classes.ReactorType,
        remove: bool,
    ):
        reactions = mes.reactions
        for reaction in reactions:
            if str(reaction) != "⭐":
                continue

            users = await reaction.users().flatten()
            user_ids = [u.id for u in users if u.id != author_id and not u.bot]

            add_ids = [
                i
                for i in user_ids
                if i not in starboard_entry.get_reactors_from_type(type_of)
            ]
            for add_id in add_ids:
                starboard_entry.add_reactor(add_id, type_of)

            if remove:
                remove_ids = [
                    i
                    for i in starboard_entry.get_reactors_from_type(type_of)
                    if i not in user_ids
                ]
                for remove_id in remove_ids:
                    starboard_entry.remove_reactor(remove_id)

            bot.starboard.upsert(starboard_entry)

    ori_mes = None
    star_mes = None

    guild = bot.get_guild(starboard_entry.guild_id)
    if not guild:
        return starboard_entry

    ori_mes_chan = guild.get_channel_or_thread(starboard_entry.ori_chan_id)
    try:
        ori_mes = await ori_mes_chan.fetch_message(starboard_entry.ori_mes_id)
        await sync_reactors(
            bot,
            ori_mes,
            starboard_entry,
            star_classes.ReactorType.ORI_REACTORS,
            remove,
        )
    except:
        pass

    starboard_chan = guild.get_channel_or_thread(starboard_entry.starboard_id)
    try:
        star_mes = await starboard_chan.fetch_message(starboard_entry.star_var_id)
        await sync_reactors(
            bot,
            star_mes,
            starboard_entry,
            star_classes.ReactorType.VAR_REACTORS,
            remove,
        )
    except:
        pass

    return starboard_entry


async def star_entry_refresh(
    bot: utils.SeraphimBase, starboard_entry: star_classes.StarboardEntry, guild_id: int
):
    # refreshes a starboard entry mes
    guild = bot.get_guild(guild_id)
    if not guild:
        return

    star_var_chan = guild.get_channel_or_thread(
        starboard_entry.starboard_id
    )  # TODO: ignore cases where bot can't access/use channel
    unique_stars = len(starboard_entry.get_reactors())

    try:
        star_var_mes = await star_var_chan.fetch_message(starboard_entry.star_var_id)
    except discord.HTTPException as e:
        # if exception: most likely this is because starboard channel has moved, so this is a fix
        if not isinstance(e, (discord.NotFound, discord.Forbidden)):
            raise e

        ori_chan = guild.get_channel_or_thread(starboard_entry.ori_chan_id)
        try:
            ori_mes = await ori_chan.fetch_message(starboard_entry.ori_mes_id)
        except discord.HTTPException:
            return

        import common.star_mes_handler  # very dirty import, i know

        star_var_mes = await common.star_mes_handler.send(bot, ori_mes)

    ori_starred = star_var_mes.embeds[0]

    if (
        unique_stars >= bot.config.getattr(guild_id, "star_limit")
        or starboard_entry.forced
    ):
        new_content = generate_content_str(starboard_entry)
        await star_var_mes.edit(content=new_content, embed=ori_starred)
    else:
        starboard_entry.star_var_id = None
        starboard_entry.starboard_id = None
        bot.starboard.upsert(starboard_entry)

        await star_var_mes.delete()
        bot.star_queue.remove_from_copy(
            (
                starboard_entry.ori_chan_id,
                starboard_entry.ori_mes_id,
                starboard_entry.guild_id,
            )
        )


async def fetch_needed(
    bot: utils.SeraphimBase, payload: discord.RawReactionActionEvent
):
    # fetches info from payload
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel_or_thread(payload.channel_id)
    mes = await channel.fetch_message(payload.message_id)

    if payload.event_type == "REACTION_ADD":
        user = payload.member
    else:
        # sadly, we have to be a bit wasteful here
        user = guild.get_member(payload.user_id)

        if user is None:  # rare, but it's happened
            try:
                user = await guild.fetch_member(payload.user_id)
            except discord.HTTPException:
                # realisitcally, this shouldn't happen much
                # we prefer a member over a user, but sometimes you gotta make due with what you have
                user = bot.get_user(
                    payload.user_id
                )  # unlikely to produce much of a result
                if user is None:
                    # last resort
                    # if this fails, will be silently ignored
                    user = await bot.fetch_user(payload.user_id)

    return user, mes.channel, mes


def star_check(bot: utils.SeraphimBase, payload):
    # basic check for starboard stuff: is it in a guild, and is the starboard enabled here?
    return bool(
        payload.guild_id and bot.config.getattr(payload.guild_id, "star_toggle")
    )
