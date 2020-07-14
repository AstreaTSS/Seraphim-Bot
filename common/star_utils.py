#!/usr/bin/env python3.7
import discord

def get_star_entry(bot, mes_id, check_for_var = False):
    if not check_for_var:
        starboard_entry = [
            bot.starboard[k] for k in bot.starboard.keys()
            if (k == mes_id or bot.starboard[k]["star_var_id"] == mes_id)
        ]
    else:
        starboard_entry = [
            bot.starboard[k] for k in bot.starboard.keys()
            if (k == mes_id or bot.starboard[k]["star_var_id"] == mes_id)
            and bot.starboard[k]["star_var_id"] != None
        ]

    return starboard_entry[0] if starboard_entry != [] else []

def get_num_stars(starboard_entry):
    reactors = get_reactor_list(starboard_entry)
    return len(reactors) if reactors != [] else 0

def get_reactor_list(starboard_entry, return_extra = False):
    ori_reactors = starboard_entry["ori_reactors"]
    var_reactors = starboard_entry["var_reactors"]

    reactors = ori_reactors + var_reactors

    if not return_extra:
        return reactors
    else:
        return {"reactors": reactors, "ori_reactors": ori_reactors, "var_reactors": var_reactors}

def clear_stars(bot, starboard_entry, mes_id):
    type_of = "ori_reactors" if mes_id == starboard_entry["ori_mes_id_bac"] else "var_reactors"
    new_reactors = []
    starboard_entry[type_of] = new_reactors

    ori_mes_id = starboard_entry["ori_mes_id_bac"]
    bot.starboard[ori_mes_id] = starboard_entry

def get_author_id(mes, bot):
    author_id = None
    if mes.author.id in [270904126974590976, 499383056822435840] and mes.embeds != []:
        dank_embed = mes.embeds[0]
        basic_author = dank_embed.author.name.split("#")
        author = discord.utils.get(mes.guild.members, name=basic_author[0], discriminator=basic_author[1])
        author_id = mes.author.id if author == None else author.id

    elif mes.author.id == bot.user.id and mes.embeds != [] and mes.embeds[0].author.name != bot.user.name:
        basic_author = mes.embeds[0].author.name.split('(', 1)[1].split(')')[0] # somehow gets stuff between parentheses
        author = discord.utils.get(mes.guild.members, name=basic_author[0], discriminator=basic_author[1])
        author_id = mes.author.id if author == None else author.id

    else:
        author_id = mes.author.id

    return author_id

async def modify_stars(bot, mes, reactor_id, operation):
    starboard_entry = get_star_entry(bot, mes.id)
    if starboard_entry == []:
        author_id = get_author_id(mes, bot)

        bot.starboard[mes.id] = {
            "ori_chan_id": mes.channel.id,
            "star_var_id": None,
            "author_id": author_id,
            "ori_reactors": reactor_id,
            "var_reactors": [],
            "guild_id": mes.guild.id,
            "forced": False,

            "ori_mes_id_bac": mes.id,
            "updated": True
        }
        starboard_entry = bot.starboard[mes.id]

        await sync_prev_reactors(bot, mes, author_id, starboard_entry, "ori_reactors")

    author_id = starboard_entry["author_id"]

    if not starboard_entry["updated"]:
        type_of = "ori_reactors" if mes.id == starboard_entry["ori_mes_id_bac"] else "var_reactors"
        await sync_prev_reactors(bot, mes, author_id, starboard_entry, type_of)

        starboard_entry = bot.starboard[starboard_entry["ori_mes_id_bac"]]
        starboard_entry["updated"] = True

    reactors = get_reactor_list(starboard_entry, return_extra=True)

    if author_id != reactor_id:
        type_of = ""

        if not reactor_id in reactors["reactors"] and operation == "ADD":
            if mes.id == starboard_entry["star_var_id"]:
                type_of = "var_reactors"
            elif mes.id == starboard_entry["ori_mes_id_bac"]:
                type_of = "ori_reactors"

            reactors[type_of].append(reactor_id)
            new_reactors = reactors[type_of]
            starboard_entry[type_of] = new_reactors

        elif operation == "SUBTRACT":
            if mes.id == starboard_entry["star_var_id"]:
                type_of = "var_reactors"
            elif mes.id == starboard_entry["ori_mes_id_bac"]:
                type_of = "ori_reactors"

            if reactor_id in reactors[type_of]:
                reactors[type_of].remove(reactor_id)
                new_reactors = reactors[type_of]

                starboard_entry[type_of] = new_reactors

        ori_mes_id = starboard_entry["ori_mes_id_bac"]
        bot.starboard[ori_mes_id] = starboard_entry

async def sync_prev_reactors(bot, mes, author_id, starboard_entry, type_of):
    reactions = mes.reactions
    for reaction in reactions:
        if str(reaction) != "⭐":
            continue

        users = await reaction.users().flatten()
        user_ids = [u.id for u in users if u.id != author_id and not u.bot]

        mes_id = starboard_entry["ori_mes_id_bac"]

        add_ids = [i.id for i in user_ids if i not in bot.starboard[mes_id][type_of]]
        remove_ids = [i.id for i in bot.starboard[mes_id][type_of] if i not in user_ids]
        for add_id in add_ids:
            bot.starboard[mes_id][type_of].append(add_id)
        for remove_id in remove_ids:
            bot.starboard[mes_id][type_of].remove(remove_id)

        return bot.starboard[mes_id][type_of]

async def star_entry_refresh(bot, starboard_entry, guild_id):
    star_var_chan = await bot.fetch_channel(bot.config[guild_id]["starboard_id"])

    try:
        star_var_mes = await star_var_chan.fetch_message(starboard_entry["star_var_id"])

        ori_starred = star_var_mes.embeds[0]
        parts = star_var_mes.content.split(" | ")

        unique_stars = get_num_stars(starboard_entry)

        if unique_stars >= bot.config[guild_id]["star_limit"] or bool(starboard_entry["forced"]):
            await star_var_mes.edit(content=f"⭐ **{unique_stars}** | {(parts)[1]}", embed=ori_starred)
        else:
            ori_mes_id = starboard_entry["ori_mes_id_bac"]
            bot.starboard[ori_mes_id]["star_var_id"] = None

            await star_var_mes.delete()
    except discord.NotFound:
        pass

def star_check(bot, payload):
    if payload.guild_id != None and bot.config[payload.guild_id]["star_toggle"]:
        return True
    
    return False