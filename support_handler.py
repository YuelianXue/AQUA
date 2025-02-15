from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def support_callback(query):
    text = "Для технической поддержки обращайтесь: support@example.com"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ])
    return text, keyboard
