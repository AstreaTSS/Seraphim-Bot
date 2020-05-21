#!/usr/bin/env python3.7
import traceback

async def fetch_needed(bot, payload):
    guild = await bot.fetch_guild(payload.guild_id)
    user = await guild.fetch_member(payload.user_id)

    channel = await bot.fetch_channel(payload.channel_id)
    mes = await channel.fetch_message(payload.message_id)

    return user, channel, mes

async def error_handle(bot, error, string = False):
    if not string:
        error_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))
    else:
        error_str = error

    application = await bot.application_info()
    owner = application.owner
    await owner.send(f"{error_str}")

    bot.logger.error(error_str)