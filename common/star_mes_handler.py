#!/usr/bin/env python3.8
import collections
import re

import discord

import common.image_utils as image_utils
import common.star_utils as star_utils
import common.utils as utils


def cant_display(embed: discord.Embed, attachments: list, index=0):
    attach_strs = collections.deque()

    for x in range(len(attachments)):
        if x < index:
            continue

        attachment = attachments[x]
        if attachment.is_spoiler():
            attach_strs.append(f"||[{attachment.filename}]({attachment.url})||")
        else:
            attach_strs.append(f"[{attachment.filename}]({attachment.url})")

    if index == 0:
        embed.add_field(name="Attachments", value="\n".join(attach_strs), inline=False)
    else:
        embed.add_field(
            name="Other Attachments", value="\n".join(attach_strs), inline=False
        )

    return embed


async def base_generate(
    bot: utils.SeraphimBase, mes: discord.Message, no_attachments: bool = False
):
    # sourcery no-metrics
    # generates core of star messages
    image_url = ""

    if (
        mes.embeds
        and mes.author.id == bot.user.id
        and mes.embeds[0].author.name != bot.user.name
        and mes.embeds[0].fields
        and mes.embeds[0].footer.text
        and mes.embeds[0].footer.text.startswith("ID:")
    ):  # all of this... for pinboard support
        send_embed = mes.embeds[
            0
        ].copy()  # it's using the same internal gen, so why not just copy it

        for x in range(len(send_embed.fields)):
            if send_embed.fields[x].name == "Original":
                send_embed.remove_field(x)
                break

        # next pieces of code make the embed more how a normally generated embed would be like
        send_embed.color = discord.Colour(0xCFCA76)
        send_embed.timestamp = mes.created_at
        send_embed.set_footer()  # will set footer to default, aka none

    elif (
        mes.embeds != []
        and mes.embeds[0].type == "rich"
        and mes.embeds[0].author.name != bot.user.name
        and isinstance(mes.embeds[0].author.icon_url, str)
        and "&userid=" in mes.embeds[0].author.icon_url
    ):  # if message is sniped message that's supported
        snipe_embed = mes.embeds[0]

        entry = await bot.starboard.get(mes.id)

        if entry:
            author = await utils.user_from_id(bot, mes.guild, entry.author_id)
        else:
            author_id = star_utils.get_author_id(mes, bot)
            author = await utils.user_from_id(bot, mes.guild, author_id)

        author_str = ""
        if author is None or author.id == bot.user.id:
            author_str = mes.embeds[0].author.name
        else:
            author_str = f"{author.display_name} ({author})"

        icon = (
            snipe_embed.author.icon_url
            if author is None or author.id == bot.user.id
            else utils.get_icon_url(author.display_avatar)
        )

        content = snipe_embed.description

        send_embed = discord.Embed(
            title="Sniped:",
            colour=discord.Colour(0xCFCA76),
            description=content,
            timestamp=mes.created_at,
        )
        send_embed.set_author(name=author_str, icon_url=icon)

    elif (
        mes.author.bot
        and mes.embeds != []
        and mes.embeds[0].description
        and mes.embeds[0].type == "rich"
        and (
            mes.embeds[0].footer.url
            != "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
            and mes.embeds[0].footer.text != "Twitter"
        )
    ):

        author = f"{mes.author.display_name} ({mes.author})"
        icon = utils.get_icon_url(mes.author.display_avatar)

        send_embed = discord.Embed(
            colour=discord.Colour(0xCFCA76),
            description=mes.embeds[0].description,
            timestamp=mes.created_at,
        )
        send_embed.set_author(name=author, icon_url=icon)

    else:
        content = utils.get_content(mes)
        author = f"{mes.author.display_name} ({mes.author})"
        icon = utils.get_icon_url(mes.author.display_avatar)

        if content:
            send_embed = discord.Embed(
                colour=discord.Colour(0xCFCA76),
                description=content,
                timestamp=mes.created_at,
            )
        else:
            send_embed = discord.Embed(
                colour=discord.Colour(0xCFCA76),
                description=None,
                timestamp=mes.created_at,
            )
        send_embed.set_author(name=author, icon_url=icon)

        if mes.type == discord.MessageType.reply:
            # checks if message has inline reply

            ref_mes_url = mes.reference.jump_url  # type: ignore

            reply_msg = await utils.resolve_reply(bot, mes)
            ref_author = reply_msg.author if reply_msg else None
            ref_auth_str = ref_author.display_name if ref_author else "a message"

            send_embed.title = f"Replying to {ref_auth_str}:"
            send_embed.url = ref_mes_url

        if (
            mes.embeds != []
            and mes.embeds[0].type == "image"
            and mes.embeds[0].thumbnail.url
        ):
            image_url = mes.embeds[0].thumbnail.url

            if not no_attachments and mes.attachments:
                send_embed = cant_display(send_embed, mes.attachments, 0)
        elif not no_attachments and mes.attachments != []:
            if (
                mes.attachments[0].proxy_url.lower().endswith(bot.image_extensions)
                and not mes.attachments[0].is_spoiler()
            ):
                image_url = mes.attachments[0].proxy_url

                if len(mes.attachments) > 1:
                    send_embed = cant_display(send_embed, mes.attachments, 1)
            else:
                send_embed = cant_display(send_embed, mes.attachments, 0)
        else:
            if not mes.flags.suppress_embeds:  # would suppress images too
                # http://urlregex.com/
                urls = re.findall(
                    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                    content,
                )
                if urls != []:
                    first_url = urls[0]

                    possible_url = await image_utils.get_image_url(first_url)
                    if possible_url != None:
                        image_url = possible_url

                # if the image url is still blank and the message has a gifv embed
                if (
                    image_url == ""
                    and mes.embeds != []
                    and mes.embeds[0].type == "gifv"
                ) and (
                    mes.embeds[0].thumbnail.url
                ):  # if there is a thumbnail url
                    image_url = mes.embeds[0].thumbnail.url

                # if the image url is STILL blank and there's a youtube video
                if (
                    image_url == ""
                    and mes.embeds
                    and mes.embeds[0].type == "video"
                    and mes.embeds[0].provider
                    and mes.embeds[0].provider.name
                    and mes.embeds[0].provider.name == "YouTube"
                ):
                    image_url = mes.embeds[0].thumbnail.url
                    send_embed.add_field(
                        name="YouTube:",
                        value=(
                            f"{mes.embeds[0].author.name}:"
                            f" [{mes.embeds[0].title}]({mes.embeds[0].url})"
                        ),
                        inline=False,
                    )

            # if the image url is STILL blank and the message has a sticker
            if image_url == "" and mes.stickers:
                if mes.stickers[0].format != discord.StickerFormatType.lottie:
                    image_url = str(mes.stickers[0].url)
                else:  # as of right now, you cannot send content with a sticker, so we might as well
                    send_embed.description = (
                        "*This message has a sticker that I cannot display. Please view"
                        " the original message to see it.*"
                    )

            if not no_attachments and mes.attachments:
                send_embed = cant_display(send_embed, mes.attachments, 0)

    if image_url != "":
        send_embed.set_image(url=image_url)

    if utils.embed_check(send_embed):
        return send_embed
    else:
        # unlikely to happen, but who knows
        raise ValueError(f"Embed was too big to process for {mes.jump_url}!")


async def star_generate(bot: utils.SeraphimBase, mes: discord.Message):
    # base generate but with more fields
    send_embed = await base_generate(bot, mes)
    send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url})", inline=True)
    send_embed.set_footer(text=f"ID: {mes.id}")

    return send_embed


async def send(bot: utils.SeraphimBase, mes: discord.Message):
    # sends message to starboard channel

    send_embed = await star_generate(bot, mes)
    star_entry = await bot.starboard.get(mes.id)
    starboard_chan = mes.guild.get_channel(
        bot.config.getattr(mes.guild.id, "starboard_id")
    )

    if starboard_chan:
        content = star_utils.generate_content_str(star_entry)
        starred = await starboard_chan.send(content=content, embed=send_embed)
        await starred.add_reaction("⭐")

        star_entry.star_var_id = starred.id
        star_entry.starboard_id = starred.channel.id
        bot.starboard.upsert(star_entry)

        return starred

    raise discord.NotFound(21234, "Unable to find starboard channel.")
