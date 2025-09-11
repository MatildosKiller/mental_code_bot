import sqlite3
import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Состояния разговора
DATE_TIME, MESSAGE = range(2)
ADMIN_CHAT_ID = 2041892313
# Инициализация базы данных
conn = sqlite3.connect('appointments.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    datetime TEXT,
    message TEXT
)
''')
conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Записаться", callback_data='make_appointment')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Добро пожаловать! Нажмите кнопку «Записаться» для записи на занятие.',
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Доступные команды:\n/start - начало работы\n/help - помощь'
    )
    await update.message.reply_text(
        'Я Добрый Бот, но к сожалению пока я еще ничего не умею!\n'
        'Я родился 04.09.2025 г.,\nно у меня впереди - увлекательная жизнь в мире IT-технологий '
        'и квантовых вычислений (шучу, вот видите, я уже умею прикалываться)'
    )
    await update.message.reply_text(
        'Впереди еще много приключений,\nвероятно их я проведу совместно с Вами и с искусственным интеллектом,\n'
        'но это пока еще мои смелые мечты\n(тссс.... они сбываются)'
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'make_appointment':
        await query.message.reply_text(
            'Пожалуйста, введите дату и время занятия в формате ДД-ММ-ГГГГ ЧЧ:ММ (например, 25-12-2024 18:30):'
        )
        return DATE_TIME
async def is_time_slot_free(dt: datetime.datetime) -> bool:
    dt_str = dt.strftime('%Y-%m-%d %H')  # Проверка только по дню и часу
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM appointments WHERE strftime('%Y-%m-%d %H', datetime) = ?",
        (dt_str,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result[0] == 0


async def is_time_slot_free(dt: datetime.datetime) -> bool:
    # Обнуляем минуты, секунды, микроcекунды — время ровно на час
    dt_hour = dt.replace(minute=0, second=0, microsecond=0)
    dt_str = dt_hour.strftime('%Y-%m-%d %H:%M')  # формат для базы
    
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM appointments WHERE datetime = ?",
        (dt_str,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result[0] == 0

async def date_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    try:
        ekb_tz = pytz.timezone('Asia/Yekaterinburg')
        dt_naive = datetime.datetime.strptime(user_input, '%d-%m-%Y %H:%M')
        dt = ekb_tz.localize(dt_naive)
        now = datetime.datetime.now(ekb_tz)

        # Проверка — не в прошлом
        if dt < now:
            await update.message.reply_text(
                "Ошибка: введённая дата и время уже прошли. Пожалуйста, введите корректную дату и время:"
            )
            return DATE_TIME

        # Проверка времени в диапазоне 09:00 - 18:00
        if dt.time() < datetime.time(9, 0) or dt.time() > datetime.time(18, 0):
            await update.message.reply_text(
                "Ошибка: время должно быть с 09:00 до 18:00. Пожалуйста, введите дату и время заново:"
            )
            return DATE_TIME

        # Проверка — до занятия не менее 1 часа
        if (dt - now).total_seconds() < 3600:
            await update.message.reply_text(
                "Ошибка: до занятия должно оставаться не менее 1 часа. Пожалуйста, введите дату и время заново:"
            )
            return DATE_TIME

        # Проверка — минуты ровно 0
        if dt.minute != 0:
            await update.message.reply_text(
                "Ошибка: время должно быть ровно на час (например, 09:00, 14:00). Пожалуйста, введите дату и время заново:"
            )
            return DATE_TIME

        # Формируем время ровно на час для проверки и записи
        dt_for_db = dt.replace(minute=0, second=0, microsecond=0)
        dt_str_db = dt_for_db.strftime('%Y-%m-%d %H:%M')

        # Проверка занятости
        is_free = await is_time_slot_free(dt_for_db)
        if not is_free:
            await update.message.reply_text(
                "Ошибка: выбранное время уже занято. Пожалуйста, выберите другое время:"
            )
            return DATE_TIME

        # Сохраняем для пользователя (в формате ДД-ММ-ГГГГ ЧЧ:ММ)
        context.user_data['datetime'] = dt.strftime('%d-%m-%Y %H:%M')

        # Вставку записи в базу (примерно, подставьте свои данные)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (user_id, username, datetime, message) VALUES (?, ?, ?, ?)",
            (update.message.from_user.id, update.message.from_user.username, dt_str_db, "")
        )
        await context.bot.send_message(
               chat_id=ADMIN_CHAT_ID, text=(
        f"Новая запись:\n"
        f"Пользователь: {update.message.from_user.full_name} (@{update.message.from_user.username})\n"
        f"Дата и время: {dt.strftime('%d-%m-%Y %H:%M')}"
    )
)
        conn.commit()
        cursor.close()

        await update.message.reply_text(
            "Вы можете добавить примечание к записи (необязательно), "
            "или отправьте команду /skip для пропуска:"
        )
        return MESSAGE

    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты и времени. Введите в формате ДД-ММ-ГГГГ ЧЧ:ММ (например, 25-12-2024 18:00)"
        )
        return DATE_TIME

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['message'] = update.message.text.strip()
    return await save_appointment(update, context)


async def skip_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['message'] = None
    await update.message.reply_text("Пропуск примечания, записываю заявку...")
    return await save_appointment(update, context)


async def save_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    dt = context.user_data.get('datetime')
    msg = context.user_data.get('message')

    cursor.execute(
        "INSERT INTO appointments (user_id, username, datetime, message) VALUES (?, ?, ?, ?)",
        (user.id, user.username or user.full_name, dt, msg)
         )
    conn.commit()

    await update.message.reply_text(f"Спасибо, ваша заявка на {dt} сохранена!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Запись отменена.')
    return ConversationHandler.END



def main():
    TOKEN = '7702037486:AAGnhxpzPKhalUu5W5MzO_RfoG0FL7V68dU'  # Замените на ваш токен бота

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^make_appointment$')],
        states={
            DATE_TIME: [MessageHandler(filters.TEXT & (~filters.COMMAND), date_time_handler)],
            MESSAGE: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler),
                CommandHandler('skip', skip_message),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(conv_handler)

    print('Добрый Бот запущен...')
    app.run_polling()


if __name__ == '__main__':
    main()
