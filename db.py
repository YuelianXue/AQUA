import sqlite3

def fetch_users(db_path="DataBase/users.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, telegram_id, first_name, last_name, username, phone, registration_date FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows

def format_users(rows):
    if not rows:
        return "No users found."
    
    # Заголовки столбцов
    header = ["ID", "Telegram ID", "First Name", "Last Name", "Username", "Phone", "Registration Date"]
    
    # Подготавливаем данные (преобразуем все элементы в строки)
    data = [list(map(str, row)) for row in rows]
    
    # Вычисляем максимальную ширину для каждого столбца (учитывая заголовки)
    columns = list(zip(header, *data))
    col_widths = [max(len(item) for item in col) for col in columns]
    
    # Формат строки с выравниванием по левому краю
    row_format = " | ".join("{:<" + str(width) + "}" for width in col_widths)
    
    # Создаем разделитель
    separator = "-+-".join("-" * width for width in col_widths)
    
    # Формируем таблицу
    lines = [row_format.format(*header), separator]
    for row in data:
        lines.append(row_format.format(*row))
    return "\n".join(lines)

if __name__ == "__main__":
    rows = fetch_users()
    table = format_users(rows)
    print(table)
