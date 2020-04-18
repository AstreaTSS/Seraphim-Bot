from discord.ext import commands
import discord

class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji == "⭐":
            channel_id = payload.channel_id
            message_id = payload.message_id
            guild_id = payload.guild_id

            mes = await self.bot.fetch_guild(guild_id).get_channel(channel_id).fetch_message(message_id)
            if not mes.author.id == payload.user_id and (not mes.author.bot or mes.author.id in [270904126974590976, 499383056822435840]):
                if mes in self.bot.mes_log[str(guild_id)]:
                    star_variant = [mes]
                else:
                    star_variant = [m for m in self.bot.mes_log[str(guild_id)] if str(message_id) in m.content]

                if star_variant is []:
                    reactions = mes.reactions
                    star_reactions = [r for r in reactions if str(r.emoji) == "⭐"]
                    reactors = [
                        u for u in await star_reactions.users().flatten() 
                        if not u.bot and not u.author.id == payload.user_id
                    ]

                    if len(reactors) >= self.bot.config_file[str(guild_id)]["limit"]:
                        files_sent = []
                        image_url = ""

                        if mes.author.id in [270904126974590976, 499383056822435840]:
                            dank_embed = mes.embeds[0]

                            basic_author = dank_embed.author.name.split("#")
                            member = discord.utils.get(mes.guild.members, name=basic_author[0], discriminator=basic_author[1])
                            author = f"{member.name}#{member.discriminator} ({member.display_name})" if member is not None else basic_author

                            icon = dank_embed.author.url
                            content = dank_embed.description

                            send_embed = discord.Embed(title="Sniped from Dank Memer:", colour=discord.Colour(0xcfca76), 
                            description=content, timestamp=mes.created_at)
                            send_embed.set_author(name=author, icon_url=icon)
                            send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url}))")
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
                            send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url}))")

                            if image_url is not "":
                                send_embed.set_image(url=image_url)
                        
                        starboard = mes.guild.get_channel(self.bot.config_file[str(guild_id)]["channel"])

                        if files_sent == []:
                            starred = await starboard.send(content=f"⭐ {len(reactors)} | {mes.channel.mention} | ID: {mes.id}", embed=send_embed)
                        else:
                            starred = await starboard.send(content=f"⭐ {len(reactors)} | {mes.channel.mention} | ID: {mes.id}", embed=send_embed, files=files_sent)
                        
                        self.bot.mes_log[guild_id].append(starred)
                else:
                    ori_starred = star_variant[0].embeds[0]

                    parts = star_variant[0].content.split(" | ")
                    num_starred = int((parts)[0].replace("⭐ ", "")) + 1

                    index = self.bot.mes_log[str(guild_id)].index(star_variant[0])
                    
                    starred = await star_variant[0].edit(content=f"⭐ {num_starred} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)

                    self.bot.mes_log[str(guild_id)][index] = starred

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.emoji == "⭐":
            channel_id = payload.channel_id
            message_id = payload.message_id
            guild_id = payload.guild_id

            mes = await self.bot.fetch_guild(guild_id).get_channel(channel_id).fetch_message(message_id)
            if not mes.author.id == payload.user_id and (not mes.author.bot or mes.author.id in [270904126974590976, 499383056822435840]):
                if mes in self.bot.mes_log[str(guild_id)]:
                    star_variant = [mes]
                else:
                    star_variant = [m for m in self.bot.mes_log[str(guild_id)] if str(message_id) in m.content]

                if star_variant is not []:
                    ori_starred = star_variant[0].embeds[0]

                    parts = star_variant[0].content.split(" | ")
                    num_starred = int((parts)[0].replace("⭐ ", "")) - 1

                    index = self.bot.mes_log[str(guild_id)].index(star_variant[0])

                    if num_starred >= self.bot.config_file[str(guild_id)]["limit"]:
                        starred = await star_variant[0].edit(content=f"⭐ {num_starred} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)
                        self.bot.mes_log[str(guild_id)][index] = starred
                    else:
                        await star_variant[0].delete()
                        del self.bot.mes_log[str(guild_id)][index]
        
def setup(bot):
    bot.add_cog(Star(bot))