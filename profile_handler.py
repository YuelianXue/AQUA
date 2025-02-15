from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from registration import get_user

async def profile_callback(query):
    user_data = get_user(query.from_user.id)
    if user_data:
        text = (
            f"Профиль:\n"
            f"Имя: {user_data['first_name']}\n"
            f"Фамилия: {user_data['last_name']}\n"
            f"Юзернейм: @{user_data['username']}\n"
            f"Телефон: {user_data['phone']}\n"
            f"Дата регистрации: {user_data['registration_date']}"
        )
    else:
        text = "Профиль не найден. Пожалуйста, авторизуйтесь, поделившись контактом."
    
    # Добавляем inline-клавиатуру с кнопкой для возврата в главное меню
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ])
    return text, keyboard
