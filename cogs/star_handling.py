from discord.ext import commands
import discord, re

class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_stars(self, mes, reactor_id, operation):
        starboard_entry = [
            self.bot.starboard[int(k)] for k in self.bot.starboard.keys()
            if (int(k) == mes.id or self.bot.starboard[int(k)]["star_var_id"] == mes.id)
            and self.bot.starboard[int(k)]["star_var_id"] != None
        ]

        if starboard_entry == []:
            self.bot.starboard[mes.id] = {
                "ori_chan_id": mes.channel.id,
                "star_var_id": None,
                "author_id": mes.author.id,
                "ori_reactors": str(reactor_id),
                "var_reactors": "",
                "ori_mes_id_bac": mes.id
            }
            starboard_entry = [self.bot.starboard[mes.id]]

        starboard_entry = starboard_entry[0]

        ori_reactors = starboard_entry["ori_reactors"].split(",")
        var_reactors = starboard_entry["var_reactors"].split(",")
        reactors = ori_reactors + var_reactors

        if not str(reactor_id) in reactors and operation == "ADD":
            if mes.channel.id == starboard_entry["var_reactors"]:
                new_reactors = ",".join(var_reactors) + f",{reactor_id}"
                starboard_entry["var_reactors"] = new_reactors
            else:
                new_reactors = ",".join(ori_reactors) + f",{reactor_id}"
                starboard_entry["ori_reactors"] = new_reactors

        elif str(reactor_id) in reactors and operation == "SUBTRACT":
            if mes.channel.id == starboard_entry["var_reactors"]:
                var_reactors.remove(str(reactor_id))
                new_reactors = ",".join(var_reactors)
                starboard_entry["var_reactors"] = new_reactors
            else:
                ori_reactors.remove(str(reactor_id))
                new_reactors = ",".join(ori_reactors)
                starboard_entry["ori_reactors"] = new_reactors

        self.bot.starboard[mes.id] = starboard_entry

        ori_reactors = starboard_entry["ori_reactors"].split(",")
        var_reactors = starboard_entry["var_reactors"].split(",")
        reactors = [i for i in ori_reactors if i != ""] + [i for i in var_reactors if i != ""]

        return len(reactors) if reactors != [] else 0

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        guild = await self.bot.fetch_guild(payload.guild_id)
        user = await guild.fetch_member(payload.user_id)

        channel = await self.bot.fetch_channel(payload.channel_id)
        mes = await channel.fetch_message(payload.message_id)

        if str(payload.emoji) == "⭐" and not user.bot and mes.author.id != user.id:

            star_variant = [
                self.bot.starboard[k] for k in self.bot.starboard.keys()
                if (k == mes.id or self.bot.starboard[k]["star_var_id"] == mes.id)
                and self.bot.starboard[k]["star_var_id"] != None
            ]

            if star_variant == []:
                unique_stars = await self.get_stars(mes, user.id, "ADD")

                if unique_stars >= self.bot.star_config[mes.guild.id]["star_limit"]:
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
                    
                    starboard = mes.guild.get_channel(self.bot.star_config[mes.guild.id]["starboard_id"])

                    if files_sent == []:
                        starred = await starboard.send(content=f"⭐ {unique_stars} | {mes.channel.mention} | ID: {mes.id}", embed=send_embed)
                        await starred.add_reaction("⭐")
                    else:
                        starred = await starboard.send(content=f"⭐ {unique_stars} | {mes.channel.mention} | ID: {mes.id}", embed=send_embed, files=files_sent)
                        await starred.add_reaction("⭐")
                    
                    self.bot.starboard[mes.id]["star_var_id"] = starred.id

            else:
                unique_stars = await self.get_stars(mes, user.id, "ADD")

                star_var_chan = await self.bot.fetch_channel(self.bot.star_config[mes.guild.id]["starboard_id"])
                star_var_mes = await star_var_chan.fetch_message(star_variant[0]["star_var_id"])

                ori_starred = star_var_mes.embeds[0]
                parts = star_var_mes.content.split(" | ")
                
                await star_var_mes.edit(content=f"⭐ {unique_stars} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = await self.bot.fetch_guild(payload.guild_id)
        user = await guild.fetch_member(payload.user_id)

        channel = await self.bot.fetch_channel(payload.channel_id)
        mes = await channel.fetch_message(payload.message_id)

        if str(payload.emoji) == "⭐" and not user.bot and mes.author.id != user.id:

            star_variant = [
                self.bot.starboard[int(k)] for k in self.bot.starboard.keys()
                if (int(k) == mes.id or self.bot.starboard[int(k)]["star_var_id"] == mes.id)
                and self.bot.starboard[int(k)]["star_var_id"] != None
            ]

            if star_variant != []:
                unique_stars = await self.get_stars(mes, user.id, "SUBTRACT")

                star_var_chan = await self.bot.fetch_channel(self.bot.star_config[mes.guild.id]["starboard_id"])
                star_var_mes = await star_var_chan.fetch_message(star_variant[0]["star_var_id"])

                ori_starred = star_var_mes.embeds[0]
                parts = star_var_mes.content.split(" | ")

                if unique_stars >= self.bot.star_config[mes.guild.id]["star_limit"]:
                    await star_var_mes.edit(content=f"⭐ {unique_stars} | {(parts)[1]} | {(parts)[2]}", embed=ori_starred)
                else:
                    ori_mes_id = star_variant[0]["ori_mes_id_bac"]
                    self.bot.starboard[ori_mes_id]["star_var_id"] = None

                    await star_var_mes.delete()
        
def setup(bot):
    bot.add_cog(Star(bot))