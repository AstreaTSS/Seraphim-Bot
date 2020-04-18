from discord.ext import commands
import discord, re

class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if str(reaction) == "⭐" and not user.bot and reaction.message.author.id != user.id:
            mes = reaction.message
            
            mes_log_messages = [v for v in self.bot.mes_log[str(mes.guild.id)].values()]
            star_variant = [m for m in mes_log_messages if mes.id == m["mes"].id]
            if star_variant == []:
                star_variant = [m for m in mes_log_messages if str(mes.id) in m["mes"].content]            

            if star_variant == []:
                unique_stars = [
                    u for u in await reaction.users().flatten()
                    if not u.bot and reaction.message.author.id != u.id
                ]

                if len(unique_stars) >= self.bot.config_file[str(mes.guild.id)]["limit"]:
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
                    
                    self.bot.mes_log[str(mes.guild.id)][starred.id] = {}
                    self.bot.mes_log[str(mes.guild.id)][starred.id]["mes"] = starred
                    self.bot.mes_log[str(mes.guild.id)][starred.id]["react"] = unique_stars
                    print(self.bot.mes_log[str(mes.guild.id)])

            else:
                check_for_mem = [u for u in self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]["react"] if user.id == u.id]
                if check_for_mem == []:
                    self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]["react"].append(user)

                    ori_starred = star_variant[0].embeds[0]
                    parts = star_variant[0].content.split(" | ")
                    
                    starred = await star_variant[0].edit(content=f"⭐ {len(unique_stars)} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)

                    self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]["mes"] = starred
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if str(reaction) == "⭐" and not user.bot and reaction.message.author.id != user.id:
            mes = reaction.message

            mes_log_messages = [v for v in self.bot.mes_log[str(mes.guild.id)].values()]
            star_variant = [m for m in mes_log_messages if mes.id == m["mes"].id]
            if star_variant == []:
                star_variant = [m for m in mes_log_messages if str(mes.id) in m["mes"].content]     

            if star_variant != []:
                check_for_mem = [u for u in self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]["react"] if user.id == u.id]
                if check_for_mem != []:
                    self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]["react"].remove(check_for_mem[0])
                    unique_stars = self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]["react"]

                    ori_starred = star_variant[0].embeds[0]
                    parts = star_variant[0].content.split(" | ")

                    if len(unique_stars) >= self.bot.config_file[str(mes.guild.id)]["limit"]:
                        starred = await star_variant[0].edit(content=f"⭐ {len(unique_stars)} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)
                        self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]["mes"] = starred
                    else:
                        await star_variant[0].delete()
                        del self.bot.mes_log[str(mes.guild.id)][star_variant[0].id]
        
def setup(bot):
    bot.add_cog(Star(bot))