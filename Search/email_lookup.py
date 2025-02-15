import re
import math
import dns.resolver
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes
import time
import asyncio

busy = False
search_done = asyncio.Event()

async def update_timer(message):
    start_time = time.time()
    while not search_done.is_set():
        elapsed = int(time.time() - start_time)
        try:
            await message.edit_text(f"Скрипт выполняется, пожалуйста, подождите... ({elapsed} сек)")
        except Exception:
            pass
        await asyncio.sleep(1)


# Увеличиваем время ожидания DNS-запросов (при необходимости)
dns.resolver.get_default_resolver().lifetime = 19


# Функция для получения DNS-информации об email
def get_email_info(email: str):
    info = {}
    try:
        domain_all = email.split('@')[-1]
    except Exception:
        domain_all = None

    try:
        name = email.split('@')[0]
    except Exception:
        name = None

    try:
        domain = re.search(r"@([^@.]+)\.", email).group(1)
    except Exception:
        domain = None

    try:
        tld = f".{email.split('.')[-1]}"
    except Exception:
        tld = None

    # MX-записи
    try:
        mx_records = dns.resolver.resolve(domain_all, 'MX')
        mx_servers = [str(record.exchange) for record in mx_records]
        info["mx_servers"] = mx_servers
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        info["mx_servers"] = None

    # SPF-записи
    try:
        spf_records = dns.resolver.resolve(domain_all, 'SPF')
        info["spf_records"] = [str(record) for record in spf_records]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        info["spf_records"] = None

    # DMARC-записи
    try:
        dmarc_records = dns.resolver.resolve(f'_dmarc.{domain_all}', 'TXT')
        info["dmarc_records"] = [str(record) for record in dmarc_records]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        info["dmarc_records"] = None

    # Пример проверки для Google Workspace / Microsoft 365
    info["google_workspace"] = False
    info["microsoft_365"] = False
    if info.get("mx_servers"):
        for server in info["mx_servers"]:
            if "google.com" in server:
                info["google_workspace"] = True
            elif "outlook.com" in server:
                info["microsoft_365"] = True

    return info, domain_all, domain, tld, name

# Функция-трекер, проверяющая наличие email на ряде сайтов
def email_tracker(email: str) -> dict:
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )

    def Instagram(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Origin': 'https://www.instagram.com',
                'Connection': 'keep-alive',
                'Referer': 'https://www.instagram.com/'
            }
            data = {"email": email}
            response = session.get("https://www.instagram.com/accounts/emailsignup/", headers=headers)
            if response.status_code != 200:
                return False
            token = session.cookies.get('csrftoken')
            if not token:
                return False
            headers["x-csrftoken"] = token
            headers["Referer"] = "https://www.instagram.com/accounts/emailsignup/"
            response = session.post(
                url="https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/",
                headers=headers,
                data=data
            )
            if response.status_code == 200:
                if "Another account is using the same email." in response.text or "email_is_taken" in response.text:
                    return True
            return False
        except Exception:
            return False

    def Twitter(email):
        try:
            session = requests.Session()
            response = session.get(
                url="https://api.twitter.com/i/users/email_available.json",
                params={"email": email}
            )
            if response.status_code == 200:
                return response.json().get("taken", False)
            return False
        except Exception:
            return False

    def Pinterest(email):
        try:
            session = requests.Session()
            response = session.get(
                "https://www.pinterest.com/_ngjs/resource/EmailExistsResource/get/",
                params={"source_url": "/", "data": '{"options": {"email": "' + email + '"}, "context": {}}'}
            )
            if response.status_code == 200:
                data = response.json()["resource_response"]
                if data.get("message") == "Invalid email.":
                    return False
                return data.get("data") is not False
            return False
        except Exception:
            return False

    def Imgur(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': '*/*',
                'Accept-Language': 'en,en-US;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://imgur.com',
                'DNT': '1',
                'Connection': 'keep-alive',
                'TE': 'Trailers',
            }
            session.get("https://imgur.com/register?redirect=%2Fuser", headers=headers)
            headers["X-Requested-With"] = "XMLHttpRequest"
            data = {'email': email}
            response = session.post('https://imgur.com/signin/ajax_email_available', headers=headers, data=data)
            if response.status_code == 200:
                data = response.json()['data']
                if data.get("available") is True or "Invalid email domain" in response.text:
                    return False
                return True
            return False
        except Exception:
            return False

    def Patreon(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': '*/*',
                'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://www.plurk.com',
                'DNT': '1',
                'Connection': 'keep-alive',
            }
            data = {'email': email}
            response = session.post('https://www.plurk.com/Users/isEmailFound', headers=headers, data=data)
            if response.status_code == 200:
                return "True" in response.text
            return False
        except Exception:
            return False

    def Spotify(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
            }
            params = {'validate': '1', 'email': email}
            response = session.get('https://spclient.wg.spotify.com/signup/public/v1/account',
                                     headers=headers, params=params)
            if response.status_code == 200:
                status = response.json().get("status", 0)
                return status == 20
            return False
        except Exception:
            return False

    def FireFox(email):
        try:
            session = requests.Session()
            data = {"email": email}
            response = session.post("https://api.accounts.firefox.com/v1/account/status", data=data)
            if response.status_code == 200:
                return "false" not in response.text.lower()
            return False
        except Exception:
            return False

    def LastPass(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': '*/*',
                'Accept-Language': 'en,en-US;q=0.5',
                'Referer': 'https://lastpass.com/',
                'X-Requested-With': 'XMLHttpRequest',
                'DNT': '1',
                'Connection': 'keep-alive',
                'TE': 'Trailers',
            }
            params = {
                'check': 'avail',
                'skipcontent': '1',
                'mistype': '1',
                'username': email,
            }
            response = session.get(
                'https://lastpass.com/create_account.php?check=avail&skipcontent=1&mistype=1&username=' +
                str(email).replace("@", "%40"), params=params, headers=headers)
            if response.status_code == 200:
                return "no" in response.text.lower()
            return False
        except Exception:
            return False

    def Archive(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': '*/*',
                'Accept-Language': 'en,en-US;q=0.5',
                'Content-Type': 'multipart/form-data; boundary=---------------------------',
                'Origin': 'https://archive.org',
                'Connection': 'keep-alive',
                'Referer': 'https://archive.org/account/signup',
                'Sec-GPC': '1',
                'TE': 'Trailers',
            }
            data = (
                '-----------------------------\r\n'
                'Content-Disposition: form-data; name="input_name"\r\n\r\nusername\r\n'
                '-----------------------------\r\n'
                'Content-Disposition: form-data; name="input_value"\r\n\r\n' + email + '\r\n'
                '-----------------------------\r\n'
                'Content-Disposition: form-data; name="input_validator"\r\n\r\ntrue\r\n'
                '-----------------------------\r\n'
                'Content-Disposition: form-data; name="submit_by_js"\r\n\r\ntrue\r\n'
                '-------------------------------\r\n'
            )
            response = session.post('https://archive.org/account/signup', headers=headers, data=data)
            if response.status_code == 200:
                return "is already taken." in response.text
            return False
        except Exception:
            return False

    def PornHub(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en,en-US;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = session.get("https://www.pornhub.com/signup", headers=headers)
            if response.status_code == 200:
                token_tag = BeautifulSoup(response.content, features="html.parser").find(attrs={"name": "token"})
                if token_tag is None:
                    return False
                token = token_tag.get("value")
            else:
                return False
            params = {'token': token}
            data = {'check_what': 'email', 'email': email}
            response = session.post('https://www.pornhub.com/user/create_account_check', headers=headers, params=params, data=data)
            if response.status_code == 200:
                if response.json().get("error_message") == "Email has been taken.":
                    return True
                return False
            return False
        except Exception:
            return False

    def Xnxx(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-en',
                'Host': 'www.xnxx.com',
                'Referer': 'https://www.google.com/',
                'Connection': 'keep-alive'
            }
            cookie = session.get('https://www.xnxx.com', headers=headers)
            if cookie.status_code != 200:
                return False
            headers['Referer'] = 'https://www.xnxx.com/somepage'
            headers['X-Requested-With'] = 'XMLHttpRequest'
            email_encoded = email.replace('@', '%40')
            response = session.get(f'https://www.xnxx.com/account/checkemail?email={email_encoded}', headers=headers, cookies=cookie.cookies)
            if response.status_code == 200:
                try:
                    if response.json().get('message') == "This email is already in use or its owner has excluded it from our website.":
                        return True
                    elif response.json().get('message') == "Invalid email address.":
                        return False
                except Exception:
                    pass    
                if response.json().get('result') == "false":
                    return True
                elif response.json().get('code') == 1:
                    return True
                elif response.json().get('result') == "true":
                    return False
                elif response.json().get('code') == 0:
                    return False  
                else:
                    return False
            return False
        except Exception:
            return False

    def Xvideo(email):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': user_agent,
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Connection': 'keep-alive',
                'Referer': 'https://www.xvideos.com/',
            }
            params = {'email': email}
            response = session.get('https://www.xvideos.com/account/checkemail', headers=headers, params=params)
            if response.status_code == 200:
                try:
                    if response.json().get('message') == "This email is already in use or its owner has excluded it from our website.":
                        return True
                    elif response.json().get('message') == "Invalid email address.":
                        return False
                except Exception:
                    pass    
                if response.json().get('result') == "false":
                    return True
                elif response.json().get('code') == 1:
                    return True
                elif response.json().get('result') == "true":
                    return False
                elif response.json().get('code') == 0:
                    return False  
                else:
                    return False
            return False
        except Exception:
            return False

    sites = [Instagram, Twitter, Pinterest, Imgur, Patreon, Spotify, FireFox,
             LastPass, Archive, PornHub, Xnxx, Xvideo]

    site_founds = []
    found = 0
    not_found = 0

    for site in sites:
        result = site(email)
        if result is True:
            site_founds.append(site.__name__)
            found += 1
        else:
            not_found += 1

    return {
        "found": found,
        "not_found": not_found,
        "sites": site_founds
    }

# Асинхронный обработчик для команды /email
def is_valid_email(email: str) -> bool:
    # Простой regex: проверяет наличие символа @ и хотя бы одной точки после него
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    return re.match(pattern, email) is not None

# Асинхронный обработчик для команды /email
import asyncio
import time
import math

async def email_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global busy, search_done
    args = context.args
    if not args:
        await update.message.reply_text("Пожалуйста, укажите email после команды, например: /email example@mail.com")
        return

    # Блокируем повторный запуск
    if busy:
        await update.message.reply_text("Поиск уже выполняется, пожалуйста, подождите...")
        return
    busy = True
    search_done.clear()

    email = args[0]

    # Проверяем формат email
    if not is_valid_email(email):
        await update.message.reply_text("Неверный формат email! Убедитесь, что указан адрес вида example@mail.com")
        busy = False
        return

    # Запускаем таймер
    progress_msg = await update.message.reply_text("Скрипт выполняется, пожалуйста, подождите... (0 сек)")
    timer_task = asyncio.create_task(update_timer(progress_msg))

    loop = asyncio.get_running_loop()
    try:
        # Вместо прямого вызова get_email_info:
        info, domain_all, domain, tld, name = await loop.run_in_executor(None, get_email_info, email)
    except Exception:
        await update.message.reply_text("Ошибка при получении информации о почте.")
        search_done.set()
        timer_task.cancel()
        busy = False
        return

    try:
        mx_servers = info["mx_servers"]
        if mx_servers:
            mx_servers = ' / '.join(mx_servers)
        else:
            mx_servers = "None"
    except Exception:
        mx_servers = "None"

    try:
        spf_records = info["spf_records"]
    except Exception:
        spf_records = "None"

    try:
        dmarc_records = info["dmarc_records"]
        if dmarc_records:
            dmarc_records = ' / '.join(dmarc_records)
        else:
            dmarc_records = "None"
    except Exception:
        dmarc_records = "None"

    try:
        google_workspace = info["google_workspace"]
    except Exception:
        google_workspace = "None"

    try:
        mailgun_validation = info.get("mailgun_validation", "None")
        if isinstance(mailgun_validation, list):
            mailgun_validation = ' / '.join(mailgun_validation)
    except Exception:
        mailgun_validation = "None"

    # Запускаем email_tracker тоже в отдельном потоке
    try:
        tracker_results = await loop.run_in_executor(None, email_tracker, email)
    except Exception:
        await update.message.reply_text("Ошибка при трекинге email.")
        search_done.set()
        timer_task.cancel()
        busy = False
        return

    total_sites = 12
    not_found_raw = tracker_results['not_found']
    vip_score = math.ceil((not_found_raw / total_sites) * 5)
    if vip_score < 1:
        vip_score = 1

    # Формируем базовую часть текста
    text = (
        f"Информация для email {email}:\n\n"
        f"  Name       : {name}\n"
        f"  Domain     : {domain}\n"
        f"  Tld        : {tld}\n"
        f"  Domain All : {domain_all}\n"
        f"  Servers    : {mx_servers}\n"
        f"  Spf        : {spf_records}\n"
        f"  Dmarc      : {dmarc_records}\n"
        f"  Workspace  : {google_workspace}\n"
        f"  Mailgun    : {mailgun_validation}\n\n"
    )

    # Если домен определён, добавляем результаты трекинга
    if domain is not None:
        tracker_text = (
            f"Tracker Results:\n"
            f"  Найденно в VIP базах : {vip_score}\n"
            f"  Найденно в FREE базах: {tracker_results['found']}\n"
            f"  Найденные в БД                   : {', '.join(tracker_results['sites'])}"
        )
        text += tracker_text

    await update.message.reply_text(text, disable_web_page_preview=True)

    # Останавливаем таймер, разблокируем поиск
    search_done.set()
    timer_task.cancel()
    busy = False

async def update_timer(message):
    import telegram.error
    start_time = time.time()
    while not search_done.is_set():
        elapsed = int(time.time() - start_time)
        new_text = f"Скрипт выполняется, пожалуйста, подождите... ({elapsed} сек)"
        try:
            await message.edit_text(new_text)
        except telegram.error.BadRequest as e:
            # Если ошибка связана с пустым текстом, завершаем цикл
            if "Message text is empty" in str(e):
                break
        except Exception:
            pass
        await asyncio.sleep(1)

# Для отладки вне Telegram
if __name__ == "__main__":
    email = input("Введите email (или 'exit' для выхода): ").strip()
    if email.lower() not in ("exit", "quit"):
        info, domain_all, domain, tld, name = get_email_info(email)
        print("DNS Info:")
        print(info)
        tracker = email_tracker(email)
        print("Tracker Results:")
        print(tracker)
