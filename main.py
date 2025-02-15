import os
import re
import logging
import asyncio
from telegram import (
    Update, 
    KeyboardButton, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)
from telegram.constants import ParseMode
from telegram.error import BadRequest
from Search.number import num_lookup, continuous_parser_task
from payment import vip_payment_paid_callback



# Импортируем функции из модуля регистрации
from registration import is_russian_number, user_exists, register_user, get_user
from profile_handler import profile_callback
from tariffs_handler import tariffs_callback
from support_handler import support_callback
from Search.email_lookup import email_lookup
from payment import vip_payment_process_callback

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_main_menu():
    instructions_text = (
        "🆘 Вы можете прислать боту запросы в следующем формате:\n\n"
        "⬇️ Примеры команд для ввода:\n\n"
        "📱 /num +79999999999 - для поиска по номеру телефона\n"
        "📨 /email elonmusk@spacex.com - для поиска по Email\n\n"
        "💰VIP ПОИСК:\n\n"
        "📱 /numvip +79999999999 - рассширенный ВИП поиск\n"
        "📨 /emailvip elonmusk@spacex.com - рассширенный вип поиск по  почте\n\n"
        "👨 Социальные сети\n"
        "├  instagram.com/username - Instagram\n"
        "├  vk.com/id1 - Вконтакте\n"
        "├  facebook.com/profile.php?id=1 - Facebook\n"
        "├  tiktok.com/@username - Tiktok\n"
        "└  ok.ru/profile/123456 - Одноклассники\n\n"
        "📧 /tgid 12345678, /tguser username - поиск по Telegram аккаунту\n"
        "🏘 /cad 77:01:0001075:1361 - поиск по кадастровому номеру\n\n"
        "📖 /tag блогер - поиск по тегам в телефонной книжке\n"
        "🏛 /company Сбербанк - поиск по юр лицам\n"
        "📑 /inn 123456789123 - поиск по ИНН\n"
        "🗂 /vy 1234567890 - проверка водительского удостоверения\n\n"

    )
    keyboard = [
        [
            InlineKeyboardButton("Профиль", callback_data="profile"),
            InlineKeyboardButton("тарифы", callback_data="tariffs")
        ],
        [InlineKeyboardButton("Тех.Поддержка", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return instructions_text, reply_markup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.
    Если пользователь уже зарегистрирован, проверяет номер:
      - Если номер не российский, выводит сообщение об отказе.
      - Если российский, отправляет главное меню.
    Если пользователь не зарегистрирован, отправляет правила сервиса и запрашивает контакт.
    """
    user = update.message.from_user
    telegram_id = user.id

    if user_exists(telegram_id):
        user_data = get_user(telegram_id)
        #ЗАПРЕТ НА ИСПОЛЬЗОВАНИЕ БОТА ДЛЯ ЛЮДЕЙ НЕ С РФ

        #if user_data and not is_russian_number(user_data["phone"]):
        #    await update.message.reply_text(
        #        "Доступ запрещён: ваш номер не из России. Пожалуйста, зарегистрируйтесь с российским номером."
        #    )
        #    return

        instructions_text, reply_markup = get_main_menu()
        await update.message.reply_text(
            instructions_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        return

    # Пользователь не зарегистрирован – отправляем правила сервиса и запрашиваем контакт
    rules_text = (
        "🗂 Правила сервиса\n\n"
        "Подтвердите, что вы ознакомлены с [политикой конфиденциальности]"
        "(https://telegra.ph/Politika-v-otnoshenii-obrabotki-personalnyh-dannyh-Telegram-bota-AQUA-02-14) "
        "и [пользовательским соглашением]"
        "(https://telegra.ph/Publichnaya-oferta-na-zaklyuchenie-licenzionnogo-dogovora-Telegram-bota-AQUA-02-14) и принимаете их условия.\n\n"
        "Обратите внимание, что пользователь несет личную ответственность за все запросы, связанные с поиском информации о людях, даже если поиск осуществляется исключительно по открытым источникам.\n\n"
    )
    await update.message.reply_text(
        rules_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
    
    contact_button = KeyboardButton("Поделиться контактом", request_contact=True)
    contact_keyboard = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, поделитесь вашим номером телефона для авторизации:",
        reply_markup=contact_keyboard
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик получения контакта:
      - Регистрирует пользователя через register_user().
      - Удаляет клавиатуру с кнопкой отправки контакта.
      - Если номер не российский, уведомляет пользователя об отказе.
      - Если номер российский, отправляет сообщение об успешной авторизации и главное меню.
    """
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Ошибка: контакт не найден. Попробуйте ещё раз.")
        return

    phone = contact.phone_number
    user = update.message.from_user
    telegram_id = user.id
    first_name = user.first_name
    last_name = user.last_name if user.last_name else ""
    username = user.username if user.username else ""

    register_user(telegram_id, first_name, last_name, username, phone)
    # Отправляем неразрывный пробел вместо пустой строки для удаления клавиатуры
    await update.message.reply_text("\u2060", reply_markup=ReplyKeyboardRemove())

    #if not is_russian_number(phone):
    #    await update.message.reply_text(
    #        "Доступ запрещён: данный номер не из России. Свяжитесь с администрацией."
    #    )
    #    return

    await update.message.reply_text("Авторизация прошла успешно!")
    instructions_text, reply_markup = get_main_menu()
    await update.message.reply_text(
        instructions_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )



async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "profile":
        result = await profile_callback(query)
    elif data in ("tariffs", "vip_1day", "vip_7day"):
        # При нажатии кнопок "tariffs", "vip_1day" или "vip_7day" вызывается tariffs_callback
        result = await tariffs_callback(query, context)
    elif data == "vip_payment_confirm":
        # При нажатии кнопки "Оплатить" вызывается функция из payment.py
        from payment import vip_payment_process_callback
        result = await vip_payment_process_callback(update, context)
    elif data == "vip_payment_paid_callback":
        from payment import vip_payment_paid_callback
        await vip_payment_paid_callback(update, context)
        return
    elif data == "support":
        result = await support_callback(query)
    elif data == "main_menu":
        instructions_text, reply_markup = get_main_menu()
        result = (instructions_text, reply_markup)
    else:
        result = ("Неизвестная команда.", None)
    
    if isinstance(result, tuple):
        text, reply_markup = result
        await query.edit_message_text(
            text=text, 
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    else:
        await query.edit_message_text(
            text=result,
            disable_web_page_preview=True
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        raise context.error
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Игнорируем эту ошибку
            return
        else:
            raise e  # Для остальных ошибок – пробрасываем

VIP_KEYWORDS = [
    "/numvip", "/emailvip", "/tgid", "/tguser", "/cad", "/tag", "/company", "/inn", "/vy",
    "instagram.com/", "vk.com/", "facebook.com/", "tiktok.com/", "ok.ru/profile/"
]

async def vip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если сообщение содержит ключевые слова VIP, сообщает, что необходима VIP подписка."""
    message_text = update.message.text.lower()
    for keyword in VIP_KEYWORDS:
        if keyword in message_text:
            await update.message.reply_text("Для использования данной функции необходима VIP подписка.")
            return

# Альтернативно, можно создать regex, который ловит эти фразы (регистронезависимо):
vip_pattern = re.compile(
    r"^(\/numvip|\/emailvip|\/tgid|\/tguser|\/cad|\/tag|\/company|\/inn|\/vy)|"
    r"(instagram\.com\/|vk\.com\/|facebook\.com\/|tiktok\.com\/|ok\.ru\/profile\/)",
    re.IGNORECASE
)

def main():
    application = ApplicationBuilder().token("").build() #введите сюда ваш токен

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CallbackQueryHandler(vip_payment_process_callback, pattern="^vip_payment_confirm$"))
    application.add_handler(CallbackQueryHandler(vip_payment_paid_callback, pattern="^vip_payment_paid$"))
    
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.Regex(vip_pattern), vip_handler))
    application.add_handler(CommandHandler("num", num_lookup))
    application.add_handler(CommandHandler("email", email_lookup))
    application.job_queue.run_repeating(continuous_parser_task, interval=60, first=0)

    application.run_polling()

if __name__ == '__main__':
    main()
