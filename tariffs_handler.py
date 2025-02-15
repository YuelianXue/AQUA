from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def tariffs_callback(query, context):
    if query.data in ("vip_1day", "vip_7day"):
        if query.data == "vip_1day":
            tariff_desc = "1 DAY - 500 RUB"
            tariff_price = 500
        elif query.data == "vip_7day":
            tariff_desc = "7 DAY - 2500 RUB"
            tariff_price = 2500
        else:
            tariff_desc = "VIP тариф"
            tariff_price = 0
        
        context.user_data["tariff_price"] = tariff_price
        
        text = (
            "💰 *VIP Доступ - Расширенный поиск*\n\n"
            f"Вы выбрали тариф *{tariff_desc}*.\n\n"
            "С данным тарифом вы получаете исключительные возможности:\n"
            "• Глубокий анализ и расширенный поиск по телефону и электронной почте\n"
            "• Детальное сканирование социальных сетей для сбора полной информации\n"
            "• Повышенная точность поиска в Telegram для выявления скрытых связей\n"
            "• Поиск по кадастровым номерам с получением детальных данных\n"
            "• Анализ тегов, юридических лиц, ИНН и проверку водительских удостоверений\n\n"
            "Оплата производится *только криптовалютой USDT*.\n\n"
            "Обратите внимание: оплата осуществляется исключительно криптой USDT в связи с недавним законом – "
            "Госдума 26 ноября приняла пакет законов, ужесточающих административную и уголовную ответственность за утечку персональных данных. "
            "Новая уголовная статья 272.1 предусматривает до шести лет лишения свободы.\n\n"
            "Нажмите кнопку *Оплатить*, чтобы создать сделку (срок сделки — 15 минут, отменить её нельзя),\n"
            "или кнопку *Назад*, чтобы вернуться к выбору тарифа."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Оплатить", callback_data="vip_payment_confirm")],
            [InlineKeyboardButton("Назад", callback_data="tariffs")]
        ])
        return text, keyboard
    else:
        # Общий экран выбора тарифов
        text = (
            "💰 *VIP Доступ*\n\n"
            "Откройте для себя расширенные возможности VIP поиска, который предоставляет:\n\n"
            "• Глубокий анализ и расширенный поиск по телефону и электронной почте\n"
            "• Детальное сканирование социальных сетей для сбора полной информации\n"
            "• Повышенная точность поиска в Telegram для выявления скрытых связей\n"
            "• Поиск по кадастровым номерам с получением детальных данных\n"
            "• Анализ тегов, юридических лиц, ИНН и проверку водительских удостоверений\n\n"
            "С VIP доступом вы получаете максимум информации и точности для эффективного поиска.\n\n"
            "*Выберите подходящий тариф:*"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("1 DAY - 500 RUB", callback_data="vip_1day"),
             InlineKeyboardButton("7 DAY - 2500 RUB", callback_data="vip_7day")],
            [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ])
        return text, keyboard
