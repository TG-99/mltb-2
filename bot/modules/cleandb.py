#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from bot import bot, LOGGER, config_dict
from bot.helper.telegram_helper.message_utils import send_message, edit_message
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import database

async def clean_database(client, message):
    buttons = ButtonMaker()
    buttons.data_button("Drop Database", "cdb database")
    buttons.data_button("All Bot Config", "cdb allconfig")
    buttons.data_button("This Bot Config", "cdb config")
    buttons.data_button("All Bot Private Files", "cdb allfiles")
    buttons.data_button("This Bot Private Files", "cdb files")
    buttons.data_button("Close", "cdb close")
    button = buttons.build_menu(2)
    await send_message(message, 'Clear Database Menu', button)

async def clean_database_update(client, query):
    message = query.message
    data = query.data.split()
    response = ""
    if data[1] == 'database':
        await database.clean_database()
        response = "Database removed!"
        LOGGER.info("Database removed!")
    elif data[1] == 'allconfig':
        await database.clean_allconfig()
        response = "All Config removed!"
        LOGGER.info("All Config removed!")
    elif data[1] == 'config':
        await database.clean_config(config_dict)
        response = "This bot Config removed!"
        LOGGER.info("This bot Config removed!")
    elif data[1] == 'allfiles':
        await database.clean_all_private_files()
        response = "All private files removed!"
        LOGGER.info("All private files removed!")
    elif data[1] == 'files':
        await database.clean_private_files(config_dict)
        response = "This bot private files removed!"
        LOGGER.info("This bot private files removed!")
    else:
        await message.reply_to_message.delete()
        await message.delete()
        return
    await query.answer()
    await edit_message(message, response)

bot.add_handler(MessageHandler(clean_database, filters=command(BotCommands.CleanDBCommand) & CustomFilters.sudo))
bot.add_handler(CallbackQueryHandler(clean_database_update, filters=regex("^cdb")))
