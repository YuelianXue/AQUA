import time
import random
import asyncio
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from telegram import Update
from telegram.ext import ContextTypes

def check_phone_in_leaks(phone_number: str) -> str:
    """
    Открывает Firefox в headless-режиме, заходит на Cybernews и проверяет наличие утечек данных по номеру.
    Возвращает текст результата.
    """
    service = Service("C:/Users/nmisa/Desktop/geckodriver.exe") #сюда вставьте расположение гекодрайвера находится в папке firefox
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    firefox_options.page_load_strategy = "normal"
    driver = webdriver.Firefox(service=service, options=firefox_options)
    try:
        driver.get("https://cybernews.com/personal-data-leak-check/#check-now")
        wait = WebDriverWait(driver, 5)

        # Ждем и находим поле ввода
        input_field = wait.until(EC.presence_of_element_located((By.ID, "email-or-phone")))
        for ch in phone_number:
            input_field.send_keys(ch)
            time.sleep(random.uniform(0.07, 0.15))

        # Кликаем по кнопке "Check now"
        check_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-js-personal-data-leak-check="action"]'))
        )
        check_button.click()

        # Ожидаем результат
        subtitle_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "p.personal-data-leak-checker-steps__header__subtitle")
            )
        )
        result_text = subtitle_element.text.strip()
        return result_text
    except Exception as e:
        return f"Ошибка: {e}"
    finally:
        driver.quit()

async def num_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /num <номер>.
    Парсит номер с помощью phonenumbers (с учетом наличия или отсутствия символа '+'),
    затем запускает Selenium-парсер для получения leak-информации.
    Пока поиск выполняется, пользователю отправляется сообщение "Скрипт выполняется, пожалуйста, подождите...".
    Результаты отправляются после завершения поиска.
    """
    args = context.args
    if not args:
        await update.message.reply_text("Пожалуйста, укажите номер после команды, например: /num 79999999999")
        return

    phone_number = args[0]
    
    # Сообщаем пользователю, что поиск запущен и нужно подождать
    await update.message.reply_text("Скрипт выполняется, пожалуйста, подождите...")
    
    try:
        if phone_number.startswith("+"):
            parsed_number = phonenumbers.parse(phone_number, None)
        else:
            parsed_number = phonenumbers.parse(phone_number, "RU")
            
        status = "Valid" if phonenumbers.is_valid_number(parsed_number) else "Invalid"
        country_code = phone_number[1:3] if phone_number.startswith("+") else "None"
        try:
            operator = carrier.name_for_number(parsed_number, "en")
        except Exception:
            operator = "None"
        try:
            type_number = "Mobile" if phonenumbers.number_type(parsed_number) == phonenumbers.PhoneNumberType.MOBILE else "Fixed"
        except Exception:
            type_number = "None"
        try:
            tzs = timezone.time_zones_for_number(parsed_number)
            timezone_info = tzs[0] if tzs else "None"
        except Exception:
            timezone_info = "None"
        try:
            country = phonenumbers.region_code_for_number(parsed_number)
        except Exception:
            country = "None"
        try:
            region = geocoder.description_for_number(parsed_number, "en")
        except Exception:
            region = "None"
        try:
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        except Exception:
            formatted_number = "None"
    except Exception as e:
        await update.message.reply_text("Неверный формат номера!")
        return

    # Запускаем Selenium-парсер в executor, чтобы не блокировать event loop
    loop = asyncio.get_running_loop()
    leak_info = await loop.run_in_executor(None, check_phone_in_leaks, phone_number)

    # Убираем нежелательную фразу из leak_info, если она присутствует
    unwanted = "Your personal data was found in the following data leaks:"
    leak_info = leak_info.replace(unwanted, "").strip()

    if "There's still a possibility of your data being leaked to an unknown database." in leak_info:
        leak_info = "ничего не найдено"

    text = (
        f"Информация для номера {phone_number}:\n\n"
        f"  Formatted    : {formatted_number}\n"
        f"  Status       : {status}\n"
        f"  Country Code : {country_code}\n"
        f"  Country      : {country}\n"
        f"  Region       : {region}\n"
        f"  Timezone     : {timezone_info}\n"
        f"  Operator     : {operator}\n"
        f"  Type Number  : {type_number}\n\n"

        f"VIP INFO    : {leak_info}"
    )

    await update.message.reply_text(text, disable_web_page_preview=True)

async def continuous_parser_task(context: ContextTypes.DEFAULT_TYPE):
    """
    Фоновая задача, которая постоянно работает.
    Параметр context необходим для совместимости с job_queue.
    """
    print("Фоновый парсер активен...")
    # Можно добавить дополнительную логику, если необходимо.
