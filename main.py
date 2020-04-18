import discord, os, asyncio
from discord.ext import commands

bot = commands.Bot(command_prefix='s!', fetch_offline_members=True)

bot.remove_command("help")

@bot.event
async def on_ready():

    bot.config_file = {}
    bot.mes_log = {}
    bot.load_extension("cogs.update_config")

    while bot.config_file == None:
        await asyncio.sleep(0.1)

    for server_id in bot.config_file.keys():
        guild = await bot.fetch_guild(int(server_id))
        starboard_channel = guild.get_channel(bot.config_file[server_id]["channel"])
        bot.mes_log[server_id] = [
            mes for mes in await starboard_channel.history(limit=None).flatten()
            if mes.author.id == bot.user.id
        ]

    cogs_list = ["cogs.star", "cogs.deleted_mes"]

    for cog in cogs_list:
        bot.load_extension(cog)

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------\n')

    activity = discord.Activity(name = 'for stars', type = discord.ActivityType.watching)
    await bot.change_presence(activity = activity)
    
@bot.check
async def block_dms(ctx):
    return ctx.guild is not None
        
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        if not isinstance(original, discord.HTTPException):
            print(original)

            application = await ctx.bot.application_info()
            owner = application.owner
            await ctx.send(f"{owner.mention}: {original}")
    elif isinstance(error, commands.ArgumentParsingError):
        await ctx.send(error)
    else:
        print(error)
        
        application = await ctx.bot.application_info()
        owner = application.owner
        await ctx.send(f"{owner.mention}: {error}")

bot.run(os.environ.get("MAIN_TOKEN"))