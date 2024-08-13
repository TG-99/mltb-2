#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from bot import bot, LOGGER, config_dict
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import DbManager

async def cleandb(client, message):
    buttons = ButtonMaker()
    buttons.ibutton("Drop Database", f"cdb database")
    buttons.ibutton("All Bot Config", f"cdb allconfig")
    buttons.ibutton("This Bot Config", f"cdb config")
    buttons.ibutton("Close", f"cdb close")
    button = buttons.build_menu(2)
    await sendMessage(message, 'Clear Database Menu', button)

async def cleandb_update(client, query):
    message = query.message
    data = query.data.split()
    if data[1] == 'database':
        await query.answer()
        await DbManager().clean_database()
        await editMessage(message, "All Database removed!")
        LOGGER.info("All Database removes!")
    elif data[1] == 'allconfig':
        await query.answer()
        await DbManager().clean_allconfig()
        await editMessage(message, "All Config removed!")
        LOGGER.info("All Config removes!")
    elif data[1] == 'config':
        await query.answer()
        await DbManager().clean_config(config_dict)
        await editMessage(message, "This bot Config removed!")
        LOGGER.info("This bot Config removes!")
    else:
        await query.answer()
        await message.reply_to_message.delete()
        await message.delete()


bot.add_handler(MessageHandler(cleandb, filters=command(BotCommands.CleanDBCommand) & CustomFilters.sudo))
bot.add_handler(CallbackQueryHandler(cleandb_update, filters=regex("^cdb")))
