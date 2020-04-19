from discord.ext import commands
import discord, re
import cogs.interact_db as db

class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_stars(self, mes, reactor_id, operation):
        starboard_entry = await db.run_command("SELECT * FROM starboard WHERE " +
            f"ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}';")

        if starboard_entry == ():
            await db.run_command("INSERT INTO starboard "+
            "(ori_mes_id, ori_chan_id, star_var_id, author_id, reactors) VALUES " +
            f"('{mes.id}', '{mes.channel.id}', NULL, '{mes.author.id}', '{reactor_id}');")

        reactors = starboard_entry[0][4].split(",")

        if not str(reactor_id) in reactors and operation == "ADD":
            new_reactors = reactors.join(",") + f",{reactor_id}"
            starboard_entry = await db.run_command(f"UPDATE starboard SET reactors = `{new_reactors}` " +
            f"WHERE ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}';")

        elif str(reactor_id) in reactors and operation == "SUBTRACT":
            reactors.remove(str(reactor_id))
            new_reactors = reactors.join(",")
            starboard_entry = await db.run_command(f"UPDATE starboard SET reactors = `{new_reactors}` " +
            f"WHERE ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}';")

        starboard_entry = await db.run_command("SELECT * FROM starboard WHERE " +
            f"ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}';")
        reactors = starboard_entry[0][4].split(",")
        return len(reactors)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if str(reaction) == "⭐" and not user.bot and reaction.message.author.id != user.id:
            mes = reaction.message

            config_file = await db.run_command(f"SELECT * FROM starboard_config WHERE server_id = {mes.guild.id}")

            star_variant = await db.run_command("SELECT * FROM starboard WHERE " +
            f"(ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}') AND " +
            f"star_var_id IS NOT NULL;")

            if star_variant == ():
                unique_stars = await self.get_stars(mes, user.id, "ADD")

                if unique_stars >= config_file[0][2]:
                    files_sent = []
                    image_url = ""

                    if mes.author.id in [270904126974590976, 499383056822435840]:
                        dank_embed = mes.embeds[0]

                        basic_author = dank_embed.author.name.split("#")
                        member = discord.utils.get(mes.guild.members, name=basic_author[0], discriminator=basic_author[1])
                        author = f"{member.name}#{member.discriminator} ({member.display_name})" if member is not None else basic_author

                        icon = dank_embed.author.icon_url
                        content = dank_embed.description

                        send_embed = discord.Embed(title="Sniped from Dank Memer:", colour=discord.Colour(0xcfca76), 
                        description=content, timestamp=mes.created_at)
                        send_embed.set_author(name=author, icon_url=icon)
                        send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url})")
                    else:
                        image_extensions = {".jpg", ".png", ".gif"}

                        if mes.attachments is not None:
                            if len(mes.attachments) == 1 and mes.attachments[0].filename.endswith(image_extensions):
                                image_url = mes.attachments[0].url
                            else:
                                for a_file in mes.attachments:
                                    to_file = await a_file.to_file()
                                    files_sent.append(to_file)

                        author = f"{mes.author.name}#{mes.author.discriminator} ({mes.author.display_name})"
                        icon = mes.author.avatar_url
                        content = mes.content

                        send_embed = discord.Embed(colour=discord.Colour(0xcfca76), description=content, timestamp=mes.created_at)
                        send_embed.set_author(name=author, icon_url=icon)
                        send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url})")

                        if image_url is not "":
                            send_embed.set_image(url=image_url)
                    
                    starboard = mes.guild.get_channel(self.bot.config_file[str(mes.guild.id)]["channel"])

                    if files_sent == []:
                        starred = await starboard.send(content=f"⭐ {len(unique_stars)} | {mes.channel.mention} | ID: {mes.id}", embed=send_embed)
                        await starred.add_reaction("⭐")
                    else:
                        starred = await starboard.send(content=f"⭐ {len(unique_stars)} | {mes.channel.mention} | ID: {mes.id}", embed=send_embed, files=files_sent)
                        await starred.add_reaction("⭐")
                    
                    await db.run_command(f"UPDATE starboard SET star_var_id = {starred.id} WHERE ori_mes_id = '{mes.id}'")

            else:
                unique_stars = await self.get_stars(mes, user.id, "ADD")

                star_var_chan = await self.bot.fetch_channel(config_file[0][0])
                star_var_mes = await star_var_chan.fetch_message(star_variant[0][2])

                ori_starred = star_var_mes.embeds[0]
                parts = star_var_mes.content.split(" | ")
                
                starred = await star_var_mes.edit(content=f"⭐ {len(unique_stars)} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if str(reaction) == "⭐" and not user.bot and reaction.message.author.id != user.id:
            mes = reaction.message

            config_file = await db.run_command(f"SELECT * FROM starboard_config WHERE server_id = {mes.guild.id}")

            star_variant = await db.run_command("SELECT * FROM starboard WHERE " +
            f"(ori_mes_id = '{mes.id}' OR star_var_id = '{mes.id}') AND " +
            f"star_var_id IS NOT NULL;")  

            if star_variant != ():
                unique_stars = await self.get_stars(mes, user.id, "SUBTRACT")

                star_var_chan = await self.bot.fetch_channel(config_file[0][0])
                star_var_mes = await star_var_chan.fetch_message(star_variant[0][2])

                ori_starred = star_var_mes.embeds[0]
                parts = star_var_mes.content.split(" | ")

                if len(unique_stars) >= config_file[0][2]:
                    await star_var_mes.edit(content=f"⭐ {len(unique_stars)} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)
                else:
                    await star_var_mes.delete()
                    await db.run_command(f"UPDATE starboard SET star_var_id = NULL WHERE star_var_id = '{star_variant[0][2]}")
        
def setup(bot):
    bot.add_cog(Star(bot))