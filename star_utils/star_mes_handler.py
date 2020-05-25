#!/usr/bin/env python3.7
import discord, re

async def send(bot, mes, unique_stars, forced = False):
    bot.starboard[mes.id]["passed_star_limit"] = True
    image_url = ""

    if mes.author.id in [270904126974590976, 499383056822435840] and mes.embeds != []:
        dank_embed = mes.embeds[0]

        basic_author = dank_embed.author.name.split("#")
        member = discord.utils.get(mes.guild.members, name=basic_author[0], discriminator=basic_author[1])
        author = f"{member.display_name} ({str(member)})" if member != None else dank_embed.author.name

        icon = dank_embed.author.icon_url if member == None else str(member.avatar_url_as(format="jpg", size=128))
        content = dank_embed.description

        send_embed = discord.Embed(title="Sniped from Dank Memer:", colour=discord.Colour(0xcfca76), 
        description=content, timestamp=mes.created_at)
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
    
    starboard = mes.guild.get_channel(bot.star_config[mes.guild.id]["starboard_id"])

    if not forced:
        starred = await starboard.send(content=f"⭐ **{unique_stars}** | {mes.channel.mention}", embed=send_embed)
    else:
        starred = await starboard.send(content=f"⭐ **{unique_stars}** | {mes.channel.mention} (Forced Entry)", embed=send_embed)
    await starred.add_reaction("⭐")
    
    bot.starboard[mes.id]["star_var_id"] = starred.id