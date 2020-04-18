import discord, os
from discord.ext import commands

bot = commands.Bot(command_prefix='s!', fetch_offline_members=True)

bot.remove_command("help")

@bot.event
async def on_ready():

    cogs_list = ["cogs.star"]

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
    if ctx.invoked_with == "dm_say":
        return ctx.guild is None
    else:
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