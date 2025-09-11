import pytz
import datetime
import sqlite3

conn = sqlite3.connect('appointments.db', check_same_thread=False)

def print_upcoming_appointments():
    ekb_tz = pytz.timezone('Asia/Yekaterinburg')
    now = datetime.datetime.now(ekb_tz).strftime('%Y-%m-%d %H:%M')
    
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, username, datetime, message FROM appointments WHERE datetime >= ? ORDER BY datetime",
        (now,)
    )
    
    rows = cursor.fetchall()
    if not rows:
        print("Записи не найдены.")
    else:
        print("Ближайшие записи:")
        for row in rows:
            user_id, username, dt_str, message = row
            print(f"- {dt_str} | {username} (ID: {user_id}) | Примечание: {message or '-'}")
    
    cursor.close()

def delete_past_appointments():
    ekb_tz = pytz.timezone('Asia/Yekaterinburg')
    now = datetime.datetime.now(ekb_tz).strftime('%Y-%m-%d %H:%M')

    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE datetime < ?", (now,))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()

    print(f"Удалено {deleted} устаревших записей.")

print("1 - просмотр новых записей, 2 - удалить старые")

res = input()
if res == '1':
    print_upcoming_appointments()
else: delete_past_appointments()
