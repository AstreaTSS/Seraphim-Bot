from discord.ext import commands
import discord, re

class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_finder = re.compile("((\w+:\/\/)[-a-zA-Z0-9:@;?&=\/%\+\.\*!'\(\),\$_\{\}\^~\[\]`#|]+)")

    async def get_stars(self, mes, reactor_id, operation):
        starboard_entry = [
            self.bot.starboard[k] for k in self.bot.starboard.keys()
            if (k == mes.id or self.bot.starboard[k]["star_var_id"] == mes.id)
        ]

        if starboard_entry == []:
            author_id = None

            if mes.author.id in [270904126974590976, 499383056822435840] and mes.embeds != []:
                dank_embed = mes.embeds[0]
                basic_author = dank_embed.author.name.split("#")
                author = discord.utils.get(mes.guild.members, name=basic_author[0], discriminator=basic_author[1])
                author_id = mes.author.id if author == None else author.id
            else:
                author_id = mes.author.id

            self.bot.starboard[mes.id] = {
                "ori_chan_id": mes.channel.id,
                "star_var_id": None,
                "author_id": author_id,
                "ori_reactors": str(reactor_id),
                "var_reactors": "",
                "ori_mes_id_bac": mes.id,
                "passed_star_limit": False
            }
            starboard_entry = [self.bot.starboard[mes.id]]

        starboard_entry = starboard_entry[0]
        author_id = starboard_entry["author_id"]

        ori_reactors = starboard_entry["ori_reactors"].split(",")
        var_reactors = starboard_entry["var_reactors"].split(",")
        reactors = ori_reactors + var_reactors

        if author_id != reactor_id:
            if not str(reactor_id) in reactors and operation == "ADD":
                print(f"{reactor_id} {reactors}")

                if mes.id == starboard_entry["star_var_id"]:
                    if var_reactors != [""]:
                        new_reactors = ",".join(var_reactors) + f",{reactor_id}"
                    else:
                        new_reactors = f"{reactor_id}"
                else:
                    if ori_reactors != [""]:
                        new_reactors = ",".join(ori_reactors) + f",{reactor_id}"
                    else:
                        new_reactors = f"{reactor_id}"
                    starboard_entry["ori_reactors"] = new_reactors

            elif operation == "SUBTRACT":
                if mes.id == starboard_entry["star_var_id"] and str(reactor_id) in var_reactors:
                    var_reactors.remove(str(reactor_id))

                    if var_reactors != []:
                        new_reactors = ",".join(var_reactors)
                    else:
                        new_reactors = ""

                    starboard_entry["var_reactors"] = new_reactors
                elif mes.id == starboard_entry["ori_mes_id_bac"] and str(reactor_id) in ori_reactors:
                    ori_reactors.remove(str(reactor_id))

                    if ori_reactors != []:
                        new_reactors = ",".join(ori_reactors)
                    else:
                        new_reactors = ""

                    starboard_entry["ori_reactors"] = new_reactors

            print(starboard_entry)
            ori_mes_id = starboard_entry["ori_mes_id_bac"]
            self.bot.starboard[ori_mes_id] = starboard_entry

        ori_reactors = starboard_entry["ori_reactors"].split(",")
        var_reactors = starboard_entry["var_reactors"].split(",")

        reactors = [i for i in ori_reactors if i != ""] + [i for i in var_reactors if i != ""]

        return len(reactors) if reactors != [] else 0

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        try:
            guild = await self.bot.fetch_guild(payload.guild_id)
            user = await guild.fetch_member(payload.user_id)

            channel = await self.bot.fetch_channel(payload.channel_id)
            mes = await channel.fetch_message(payload.message_id)
        except discord.HTTPException:
            print(f"{payload.message_id}: could not find Message object. Channel: {payload.channel_id}")
            return

        if (str(payload.emoji) == "⭐" and not user.bot and mes.author.id != user.id
            and not str(channel.id) in self.bot.star_config[mes.guild.id]["blacklist"].split(",")):

            star_variant = [
                self.bot.starboard[k] for k in self.bot.starboard.keys()
                if (k == mes.id or self.bot.starboard[k]["star_var_id"] == mes.id)
                and self.bot.starboard[k]["star_var_id"] != None
            ]

            if star_variant == []:
                if channel.id != self.bot.star_config[mes.guild.id]["starboard_id"]:
                    unique_stars = await self.get_stars(mes, user.id, "ADD")

                    if unique_stars >= self.bot.star_config[mes.guild.id]["star_limit"]:
                        if not self.bot.starboard[mes.id]["passed_star_limit"]:
                            self.bot.starboard[mes.id]["passed_star_limit"] = True
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
                                    if len(mes.attachments) == 1 and mes.attachments[0].filename.endswith(image_extensions):
                                        image_url = mes.attachments[0].url
                                    else:
                                        if content != "":
                                            content += "\n\n"
                                        content += "*This message has attachments the bot cannot display. Pleae check out the original message to see them.*"

                                urls = self.url_finder.findall(content)
                                if urls != []:
                                    images = [url[0] for url in urls if url[0].endswith(image_extensions)]
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
                            
                            starboard = mes.guild.get_channel(self.bot.star_config[mes.guild.id]["starboard_id"])

                            starred = await starboard.send(content=f"⭐ **{unique_stars}** | {mes.channel.mention}", embed=send_embed)
                            await starred.add_reaction("⭐")
                            
                            self.bot.starboard[mes.id]["star_var_id"] = starred.id
                            
            elif user.id != star_variant[0]["author_id"]:
                unique_stars = await self.get_stars(mes, user.id, "ADD")
                star_var_chan = await self.bot.fetch_channel(self.bot.star_config[mes.guild.id]["starboard_id"])

                try:
                    star_var_mes = await star_var_chan.fetch_message(star_variant[0]["star_var_id"])

                    ori_starred = star_var_mes.embeds[0]
                    parts = star_var_mes.content.split(" | ")
                    
                    await star_var_mes.edit(content=f"⭐ **{unique_stars}** | {(parts)[1]}", embed=ori_starred)
                except discord.NotFound:
                    do_nothing = True
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = await self.bot.fetch_guild(payload.guild_id)
        user = await guild.fetch_member(payload.user_id)

        channel = await self.bot.fetch_channel(payload.channel_id)
        mes = await channel.fetch_message(payload.message_id)

        if (str(payload.emoji) == "⭐" and not user.bot and mes.author.id != user.id
            and not str(channel.id) in self.bot.star_config[mes.guild.id]["blacklist"].split(",")):

            star_variant = [
                self.bot.starboard[int(k)] for k in self.bot.starboard.keys()
                if (int(k) == mes.id or self.bot.starboard[int(k)]["star_var_id"] == mes.id)
            ]

            if star_variant != []:
                unique_stars = await self.get_stars(mes, user.id, "SUBTRACT")

                if star_variant[0]["star_var_id"] != None:
                    star_var_chan = await self.bot.fetch_channel(self.bot.star_config[mes.guild.id]["starboard_id"])

                    try:
                        star_var_mes = await star_var_chan.fetch_message(star_variant[0]["star_var_id"])

                        ori_starred = star_var_mes.embeds[0]
                        parts = star_var_mes.content.split(" | ")

                        if unique_stars >= self.bot.star_config[mes.guild.id]["star_limit"]:
                            await star_var_mes.edit(content=f"⭐ **{unique_stars}** | {(parts)[1]}", embed=ori_starred)
                        else:
                            ori_mes_id = star_variant[0]["ori_mes_id_bac"]
                            self.bot.starboard[ori_mes_id]["star_var_id"] = None

                            await star_var_mes.delete()
                    except discord.NotFound:
                        do_nothing = True
        
def setup(bot):
    bot.add_cog(Star(bot))