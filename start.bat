@echo off


echo Скрипт запущен с правами администратора.
echo -----------------------------------------

:: Ниже можно добавить ваши команды:
:: 1) Обновление pip
python -m pip install --upgrade pip

:: 2) Установка зависимостей
python -m pip install python-telegram-bot requests beautifulsoup4 dnspython phonenumbers selenium

:: 3) Проверка и установка Firefox
if exist "C:\Program Files\Mozilla Firefox\firefox.exe" (
    echo Firefox уже установлен.
) else if exist "C:\Program Files (x86)\Mozilla Firefox\firefox.exe" (
    echo Firefox уже установлен.
) else (
    echo Запуск установки Firefox...
    start "" /wait "firefox\Firefox Installer.exe"
)

:: 4) Запуск main.py
python main.py

pause
