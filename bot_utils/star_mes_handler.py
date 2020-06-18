#!/usr/bin/env python3.7
import discord, re

import bot_utils.star_universals as star_univ
import bot_utils.universals as univ

async def send(bot, mes, unique_stars, forced = False):
    image_url = ""

    if mes.embeds != [] and (mes.author.id in [270904126974590976, 499383056822435840]
    or (mes.author.id == bot.user.id and mes.embeds[0].author.name != bot.user.name)):
        snipe_embed = mes.embeds[0]

        entry = star_univ.get_star_entry(bot, mes.id)

        author = univ.user_from_id(bot, mes.guild, entry["author_id"])
        author_str = ""
        if author == None:
            author_str = mes.embeds[0].author.name
        else:
            author_str = f"{author.display_name} ({str(author)})"

        icon = snipe_embed.author.icon_url if author == None else str(author.avatar_url_as(format="jpg", size=128))
        content = snipe_embed.description

        send_embed = discord.Embed(title="Sniped:", colour=discord.Colour(0xcfca76), 
        description=content, timestamp=mes.created_at)
        send_embed.set_author(name=author_str, icon_url=icon)
        send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url})")
        send_embed.set_footer(text=f"ID: {mes.id}")

    elif mes.embeds != [] and mes.embeds[0].description != discord.Embed.Empty:
        author = f"{mes.author.display_name} ({str(mes.author)})"
        icon = str(mes.author.avatar_url_as(format="jpg", size=128))

        send_embed = discord.Embed(colour=discord.Colour(0xcfca76), description=mes.embeds[0].description, timestamp=mes.created_at)
        send_embed.set_author(name=author, icon_url=icon)
        send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url})")
        send_embed.set_footer(text=f"ID: {mes.id}")
        
    else:
        content = mes.content

        image_endings = (".jpg", ".png", ".gif")
        image_extensions = tuple(image_endings) # no idea why I have to do this

        if mes.attachments != []:
            if len(mes.attachments) == 1 and mes.attachments[0].filename.lower().endswith(image_extensions):
                image_url = mes.attachments[0].url
            else:
                if content != "":
                    content += "\n\n"
                content += "*This message has attachments the bot cannot display. Pleae check out the original message to see them.*"

        urls = re.findall(r"((\w+:\/\/)[-a-zA-Z0-9:@;?&=\/%\+\.\*!'\(\),\$_\{\}\^~\[\]`#|]+)", content)
        if urls != []:
            images = [url[0] for url in urls if url[0].lower().endswith(image_extensions)]
            if images != []:
                image_url = images[0]

        author = f"{mes.author.display_name} ({str(mes.author)})"
        icon = str(mes.author.avatar_url_as(format="jpg", size=128))

        if content != "":
            send_embed = discord.Embed(colour=discord.Colour(0xcfca76), description=content, timestamp=mes.created_at)
        else:
            send_embed = discord.Embed(colour=discord.Colour(0xcfca76), description=discord.Embed.Empty, timestamp=mes.created_at)
        send_embed.set_author(name=author, icon_url=icon)
        send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url})")
        send_embed.set_footer(text=f"ID: {mes.id}")

        if image_url != "":
            send_embed.set_image(url=image_url)
    
    starboard = mes.guild.get_channel(bot.config[mes.guild.id]["starboard_id"])

    if not forced:
        starred = await starboard.send(content=f"⭐ **{unique_stars}** | {mes.channel.mention}", embed=send_embed)
    else:
        starred = await starboard.send(content=f"⭐ **{unique_stars}** | {mes.channel.mention} (Forced Entry)", embed=send_embed)
    await starred.add_reaction("⭐")
    
    bot.starboard[mes.id]["star_var_id"] = starred.id