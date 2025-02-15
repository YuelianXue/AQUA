import random
import string
import uuid
import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
import asyncio


# Фиксированный курс обмена: 98 руб. за 1 USD (можно менять)
CONVERSION_RATE = 98

def generate_transaction_number():
    # Генерируем случайный номер сделки: 10 символов (буквы и цифры)
    return uuid.uuid4().hex[:10].upper()

def generate_random_comment(length=6):
    # Генерируем случайный комментарий из букв и цифр
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

async def vip_payment_process_callback(update, context):
    """
    Обработчик нажатия кнопки "Оплатить" (callback_data "vip_payment_confirm").
    Бот отправляет сообщение с инструкциями по переводу USDT через криптобота,
    рассчитывает сумму в долларах, генерирует случайный номер сделки и комментарий.
    Под сообщением выводятся кнопки "Оплатил" и "Главное меню".
    """
    query = update.callback_query
    await query.answer()

    tariff_price_rub = context.user_data.get("tariff_price", 500)
    tariff_price_usd = tariff_price_rub / CONVERSION_RATE

    transaction_number = generate_transaction_number()
    random_comment = generate_random_comment()

    text = (
        "💳 *Подтверждение оплаты VIP тарифа*\n\n"
        "Пожалуйста, переведите USDT через криптобота по следующей ссылке:\n"
        "t.me/send?start=IVOWWDchBeV1\n\n"
        f"Сумма для перевода: *{tariff_price_rub} RUB* (примерно *{tariff_price_usd:.2f} USD*).\n\n"
        f"Ваш комментарий к платежу: *{random_comment}*\n"
        f"Номер сделки: *{transaction_number}*\n\n"
        "После перевода нажмите кнопку *Оплатил*, чтобы подтвердить оплату.\n"
        "Обратите внимание: сделка будет действовать в течение 15 минут, после чего, если оплата не подтверждена, она будет отменена."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Оплатил", callback_data="vip_payment_paid_callback")],
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ])
    # Здесь можно добавить код для сохранения сделки в БД

    return text, keyboard



async def vip_payment_paid_callback(update, context):
    """
    Обработчик нажатия кнопки "Оплатил" (callback_data "vip_payment_paid").
    Сначала отправляет сообщение "Ожидаем платеж...", затем через задержку отправляет новое сообщение с главным меню.
    """
    query = update.callback_query
    await query.answer()
    
    # Отправляем новое сообщение со статусом ожидания платежа
    await query.message.reply_text("Ожидаем платеж... \n\n Вам придет уведомление как поступит платеж, в ином случае свяжитесь с тех.поддержкой \n\n Возвращение в главное меню", parse_mode=ParseMode.MARKDOWN)
    
    # Задержка на 5 секунд (настройте по необходимости)
    await asyncio.sleep(5)
    
    # Импортируем функцию get_main_menu из main.py (убедитесь, что она возвращает непустой текст и клавиатуру)
    from main import get_main_menu
    instructions_text, reply_markup = get_main_menu()
    
    # Отправляем новое сообщение с главным меню
    await query.message.reply_text(
         text=instructions_text,
         reply_markup=reply_markup,
         parse_mode=ParseMode.MARKDOWN,
         disable_web_page_preview=True
    )