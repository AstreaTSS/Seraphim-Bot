import discord, os, asyncio
from discord.ext import commands

async def _prefix(bot, msg):
    bot_id = bot.user.id
    mentioned = f"<@{bot_id}>"

    return [mentioned, "s?"]

bot = commands.Bot(command_prefix=_prefix, fetch_offline_members=True)

bot.remove_command("help")

@bot.event
async def on_ready():
    bot.starboard = {}
    bot.star_config = {}
    bot.load_extension("cogs.db_handler")
    while bot.star_config == {} or bot.starboard == {}:
        await asyncio.sleep(0.1)

    cogs_list = ["cogs.star_handling", "cogs.clear_events", "cogs.commands"]

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