import json
import os
import psycopg2
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

def handler(event: dict, context) -> dict:
    """
    Webhook обработчик для Telegram бота знакомств.
    Обрабатывает команды, callback'и и сообщения от пользователей.
    """
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        update = json.loads(event.get('body', '{}'))
        
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        db_url = os.environ.get('DATABASE_URL')
        schema = os.environ.get('MAIN_DB_SCHEMA', 'public')
        
        if not bot_token or not db_url:
            return error_response('Missing configuration')
        
        conn = psycopg2.connect(db_url, options=f'-c search_path={schema}')
        conn.autocommit = True
        cursor = conn.cursor()
        
        response = process_update(update, bot_token, cursor, schema)
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }
        
    except Exception as e:
        return error_response(str(e))


def process_update(update: dict, bot_token: str, cursor, schema: str) -> dict:
    """Обработка входящего обновления от Telegram"""
    
    if 'message' in update:
        return handle_message(update['message'], bot_token, cursor, schema)
    
    if 'callback_query' in update:
        return handle_callback(update['callback_query'], bot_token, cursor, schema)
    
    return {'ok': True}


def handle_message(message: dict, bot_token: str, cursor, schema: str) -> dict:
    """Обработка текстовых сообщений и команд"""
    
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user = message['from']
    
    admin_id = os.environ.get('ADMIN_TELEGRAM_ID', '')
    is_admin = str(chat_id) == admin_id
    
    if text == '/start':
        msg = "💜 Добро пожаловать в бот знакомств для подростков!\n\n"
        msg += "Здесь ты можешь найти новых друзей.\n\n"
        msg += "Используй команды:\n"
        msg += "/create - Создать анкету\n"
        msg += "/browse - Смотреть анкеты\n"
        msg += "/matches - Взаимные лайки\n"
        msg += "/profile - Моя анкета\n"
        msg += "/help - Помощь\n"
        
        if is_admin:
            msg += "\n🛡️ Команды модератора:\n"
            msg += "/moderate - Проверить анкеты\n"
            msg += "/reports - Просмотреть жалобы\n"
            msg += "/stats - Статистика бота"
        
        return send_message(bot_token, chat_id, msg)
    
    if text == '/create':
        profile = get_profile(cursor, chat_id)
        if profile:
            return send_message(bot_token, chat_id, "У тебя уже есть анкета! Используй /profile чтобы её посмотреть.")
        
        return send_message(
            bot_token,
            chat_id,
            "Давай создадим твою анкету! 📝\n\n"
            "Отправь мне информацию в формате:\n\n"
            "Имя\n"
            "Возраст (13-19)\n"
            "Город\n"
            "Пол (М/Ж)\n"
            "О себе\n\n"
            "Например:\n"
            "Алексей\n"
            "16\n"
            "Москва\n"
            "М\n"
            "Увлекаюсь программированием"
        )
    
    if text == '/browse':
        profile = get_profile(cursor, chat_id)
        if not profile:
            return send_message(bot_token, chat_id, "Сначала создай анкету командой /create")
        
        if profile[9] != 'approved':
            return send_message(bot_token, chat_id, "Твоя анкета ещё не одобрена модератором. Подожди немного!")
        
        likes_today = count_likes_today(cursor, chat_id)
        if likes_today >= 15:
            return send_message(bot_token, chat_id, "Лимит лайков исчерпан (15/15). Приходи завтра! 🌙")
        
        next_profile = get_next_profile(cursor, chat_id)
        if not next_profile:
            return send_message(bot_token, chat_id, "Пока нет новых анкет. Загляни позже!")
        
        return show_profile_card(bot_token, chat_id, next_profile, likes_today)
    
    if text == '/matches':
        profile = get_profile(cursor, chat_id)
        if not profile:
            return send_message(bot_token, chat_id, "Сначала создай анкету командой /create")
        
        matches = get_matches(cursor, chat_id)
        if not matches:
            return send_message(bot_token, chat_id, "Пока нет взаимных лайков 💔\n\nПродолжай смотреть анкеты!")
        
        text = "💜 Взаимные симпатии:\n\n"
        for match in matches:
            text += f"👤 {match[3]}, {match[4]} — @{match[2] or 'нет username'}\n"
        
        return send_message(bot_token, chat_id, text)
    
    if text == '/profile':
        profile = get_profile(cursor, chat_id)
        if not profile:
            return send_message(bot_token, chat_id, "У тебя ещё нет анкеты. Создай её командой /create")
        
        status_emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}
        status_text = {'pending': 'На модерации', 'approved': 'Одобрено', 'rejected': 'Отклонено'}
        
        text = (
            f"📋 Твоя анкета:\n\n"
            f"Имя: {profile[3]}\n"
            f"Возраст: {profile[4]}\n"
            f"Город: {profile[5]}\n"
            f"Пол: {'Парень' if profile[6] == 'male' else 'Девушка'}\n"
        )
        
        if profile[8]:
            text += f"О себе: {profile[8]}\n"
        
        text += f"\nСтатус: {status_emoji[profile[9]]} {status_text[profile[9]]}"
        
        return send_message(bot_token, chat_id, text)
    
    if text == '/moderate':
        if not is_admin:
            return send_message(bot_token, chat_id, "У вас нет доступа к этой команде")
        return show_pending_profiles(bot_token, chat_id, cursor)
    
    if text == '/reports':
        if not is_admin:
            return send_message(bot_token, chat_id, "У вас нет доступа к этой команде")
        return show_reports(bot_token, chat_id, cursor)
    
    if text == '/stats':
        if not is_admin:
            return send_message(bot_token, chat_id, "У вас нет доступа к этой команде")
        return show_stats(bot_token, chat_id, cursor)
    
    if text == '/help':
        return send_message(
            bot_token,
            chat_id,
            "ℹ️ Помощь:\n\n"
            "🔹 Создай анкету командой /create\n"
            "🔹 Просматривай анкеты - /browse\n"
            "🔹 Ставь лайки (15 в день)\n"
            "🔹 При взаимном лайке откроется username\n"
            "🔹 Все анкеты проверяет модератор\n\n"
            "⚠️ Правила:\n"
            "- Возраст 13-19 лет\n"
            "- Уважительное общение\n"
            "- Реальные фото\n\n"
            "По вопросам: /report"
        )
    
    lines = text.strip().split('\n')
    if len(lines) >= 4:
        profile = get_profile(cursor, chat_id)
        if not profile:
            return create_profile_from_text(bot_token, chat_id, user, lines, cursor)
    
    return send_message(bot_token, chat_id, "Используй команды: /start, /create, /browse, /matches, /profile, /help")


def handle_callback(callback: dict, bot_token: str, cursor, schema: str) -> dict:
    """Обработка нажатий на кнопки"""
    
    data = callback['data']
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    
    if data.startswith('like_'):
        target_id = int(data.split('_')[1])
        return handle_like(bot_token, chat_id, target_id, cursor, message_id)
    
    if data.startswith('skip_'):
        return handle_skip(bot_token, chat_id, message_id)
    
    if data.startswith('report_'):
        target_id = int(data.split('_')[1])
        return handle_report(bot_token, chat_id, target_id, cursor, message_id)
    
    if data.startswith('mod_approve_'):
        profile_id = int(data.split('_')[2])
        return mod_approve_profile(bot_token, chat_id, profile_id, cursor, message_id)
    
    if data.startswith('mod_reject_'):
        profile_id = int(data.split('_')[2])
        return mod_reject_profile(bot_token, chat_id, profile_id, cursor, message_id)
    
    if data.startswith('rep_resolve_'):
        report_id = int(data.split('_')[2])
        return mod_resolve_report(bot_token, chat_id, report_id, cursor, message_id)
    
    if data.startswith('rep_dismiss_'):
        report_id = int(data.split('_')[2])
        return mod_dismiss_report(bot_token, chat_id, report_id, cursor, message_id)
    
    return {'ok': True}


def handle_like(bot_token: str, chat_id: int, target_id: int, cursor, message_id: int) -> dict:
    """Обработка лайка"""
    
    likes_today = count_likes_today(cursor, chat_id)
    if likes_today >= 15:
        answer_callback(bot_token, chat_id, "Лимит лайков исчерпан (15/15)")
        return {'ok': True}
    
    cursor.execute(
        "INSERT INTO likes (from_user_id, to_user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (chat_id, target_id)
    )
    
    cursor.execute(
        "SELECT 1 FROM likes WHERE from_user_id = %s AND to_user_id = %s",
        (target_id, chat_id)
    )
    
    is_mutual = cursor.fetchone() is not None
    
    if is_mutual:
        cursor.execute(
            "INSERT INTO matches (user1_id, user2_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (min(chat_id, target_id), max(chat_id, target_id))
        )
        
        cursor.execute(
            "SELECT name, username FROM profiles WHERE telegram_id = %s",
            (target_id,)
        )
        target = cursor.fetchone()
        
        send_message(
            bot_token,
            chat_id,
            f"💜 Взаимная симпатия!\n\nВы можете написать: @{target[1] or 'нет username'}"
        )
        
        send_message(
            bot_token,
            target_id,
            f"💜 Взаимная симпатия!\n\nВы можете написать: @{chat_id}"
        )
    else:
        send_message(bot_token, chat_id, "❤️ Лайк отправлен!")
    
    delete_message(bot_token, chat_id, message_id)
    
    next_profile = get_next_profile(cursor, chat_id)
    if next_profile:
        show_profile_card(bot_token, chat_id, next_profile, likes_today + 1)
    else:
        send_message(bot_token, chat_id, "Пока нет новых анкет. Загляни позже!")
    
    return {'ok': True}


def handle_skip(bot_token: str, chat_id: int, message_id: int) -> dict:
    """Пропуск анкеты"""
    delete_message(bot_token, chat_id, message_id)
    send_message(bot_token, chat_id, "Используй /browse чтобы смотреть анкеты дальше")
    return {'ok': True}


def handle_report(bot_token: str, chat_id: int, target_id: int, cursor, message_id: int) -> dict:
    """Жалоба на пользователя"""
    
    cursor.execute(
        "INSERT INTO reports (reporter_id, reported_user_id, reason) VALUES (%s, %s, %s)",
        (chat_id, target_id, 'Жалоба через бота')
    )
    
    send_message(bot_token, chat_id, "Жалоба отправлена модератору. Спасибо!")
    delete_message(bot_token, chat_id, message_id)
    
    return {'ok': True}


def create_profile_from_text(bot_token: str, chat_id: int, user: dict, lines: list, cursor) -> dict:
    """Создание анкеты из текста"""
    
    try:
        name = lines[0].strip()
        age = int(lines[1].strip())
        city = lines[2].strip()
        gender = 'male' if lines[3].strip().upper() in ['М', 'M', 'ПАРЕНЬ'] else 'female'
        bio = lines[4].strip() if len(lines) > 4 else ''
        
        if age < 13 or age > 19:
            return send_message(bot_token, chat_id, "Возраст должен быть от 13 до 19 лет")
        
        username = user.get('username', '')
        
        cursor.execute(
            """INSERT INTO profiles (telegram_id, username, name, age, city, gender, photo_url, bio, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (chat_id, username, name, age, city, gender, 'https://via.placeholder.com/400', bio, 'pending')
        )
        
        return send_message(
            bot_token,
            chat_id,
            "✅ Анкета создана и отправлена на модерацию!\n\n"
            "Администратор проверит её в ближайшее время.\n"
            "После одобрения ты сможешь смотреть анкеты других пользователей."
        )
        
    except (ValueError, IndexError):
        return send_message(bot_token, chat_id, "Неверный формат. Попробуй ещё раз командой /create")


def get_profile(cursor, telegram_id: int) -> Optional[tuple]:
    """Получить профиль пользователя"""
    cursor.execute("SELECT * FROM profiles WHERE telegram_id = %s", (telegram_id,))
    return cursor.fetchone()


def get_next_profile(cursor, my_id: int) -> Optional[tuple]:
    """Получить следующую анкету для просмотра"""
    cursor.execute(
        """SELECT * FROM profiles 
           WHERE telegram_id != %s 
           AND status = 'approved'
           AND telegram_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = %s)
           ORDER BY RANDOM()
           LIMIT 1""",
        (my_id, my_id)
    )
    return cursor.fetchone()


def get_matches(cursor, my_id: int) -> list:
    """Получить список взаимных лайков"""
    cursor.execute(
        """SELECT p.* FROM profiles p
           INNER JOIN matches m ON (p.telegram_id = m.user1_id OR p.telegram_id = m.user2_id)
           WHERE (m.user1_id = %s OR m.user2_id = %s) AND p.telegram_id != %s""",
        (my_id, my_id, my_id)
    )
    return cursor.fetchall()


def count_likes_today(cursor, my_id: int) -> int:
    """Подсчитать лайки за сегодня"""
    cursor.execute(
        "SELECT COUNT(*) FROM likes WHERE from_user_id = %s AND created_at > NOW() - INTERVAL '24 hours'",
        (my_id,)
    )
    return cursor.fetchone()[0]


def show_profile_card(bot_token: str, chat_id: int, profile: tuple, likes_count: int) -> dict:
    """Показать карточку анкеты с кнопками"""
    
    gender_text = 'Парень' if profile[6] == 'male' else 'Девушка'
    text = (
        f"👤 {profile[3]}, {profile[4]}\n"
        f"📍 {profile[5]}\n"
        f"👥 {gender_text}\n"
    )
    
    if profile[8]:
        text += f"\n💬 {profile[8]}\n"
    
    text += f"\n❤️ Лайков сегодня: {likes_count}/15"
    
    keyboard = {
        'inline_keyboard': [
            [
                {'text': '❌ Пропустить', 'callback_data': f'skip_{profile[1]}'},
                {'text': '❤️ Лайк', 'callback_data': f'like_{profile[1]}'}
            ],
            [
                {'text': '🚩 Пожаловаться', 'callback_data': f'report_{profile[1]}'}
            ]
        ]
    }
    
    import requests
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            'chat_id': chat_id,
            'text': text,
            'reply_markup': keyboard
        }
    )
    
    return {'ok': True}


def send_message(bot_token: str, chat_id: int, text: str) -> dict:
    """Отправить текстовое сообщение"""
    import requests
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={'chat_id': chat_id, 'text': text}
    )
    return {'ok': True}


def delete_message(bot_token: str, chat_id: int, message_id: int):
    """Удалить сообщение"""
    import requests
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/deleteMessage",
        json={'chat_id': chat_id, 'message_id': message_id}
    )


def answer_callback(bot_token: str, callback_id: int, text: str):
    """Ответить на callback"""
    import requests
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery",
        json={'callback_query_id': callback_id, 'text': text}
    )


def show_pending_profiles(bot_token: str, chat_id: int, cursor) -> dict:
    """Показать анкеты на модерации"""
    cursor.execute(
        "SELECT id, telegram_id, name, age, city, gender, bio FROM profiles WHERE status = 'pending' ORDER BY created_at LIMIT 1"
    )
    
    profile = cursor.fetchone()
    if not profile:
        return send_message(bot_token, chat_id, "✅ Нет анкет на модерации")
    
    gender_text = 'Парень' if profile[5] == 'male' else 'Девушка'
    text = (
        f"🔍 Анкета на проверку:\n\n"
        f"👤 {profile[2]}, {profile[3]}\n"
        f"📍 {profile[4]}\n"
        f"👥 {gender_text}\n"
    )
    
    if profile[6]:
        text += f"💬 {profile[6]}\n"
    
    text += f"\n🆔 Telegram ID: {profile[1]}"
    
    keyboard = {
        'inline_keyboard': [
            [
                {'text': '❌ Отклонить', 'callback_data': f'mod_reject_{profile[0]}'},
                {'text': '✅ Одобрить', 'callback_data': f'mod_approve_{profile[0]}'}
            ]
        ]
    }
    
    import requests
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={'chat_id': chat_id, 'text': text, 'reply_markup': keyboard}
    )
    
    return {'ok': True}


def show_reports(bot_token: str, chat_id: int, cursor) -> dict:
    """Показать жалобы"""
    cursor.execute(
        """SELECT r.id, r.reporter_id, r.reported_user_id, r.reason,
                  p1.name as reporter_name, p2.name as reported_name
           FROM reports r
           JOIN profiles p1 ON r.reporter_id = p1.telegram_id
           JOIN profiles p2 ON r.reported_user_id = p2.telegram_id
           WHERE r.status = 'pending'
           ORDER BY r.created_at
           LIMIT 1"""
    )
    
    report = cursor.fetchone()
    if not report:
        return send_message(bot_token, chat_id, "✅ Нет активных жалоб")
    
    text = (
        f"🚩 Жалоба #{report[0]}:\n\n"
        f"От: {report[4]} (ID: {report[1]})\n"
        f"На: {report[5]} (ID: {report[2]})\n"
    )
    
    if report[3]:
        text += f"\nПричина: {report[3]}"
    
    keyboard = {
        'inline_keyboard': [
            [
                {'text': '❌ Отклонить', 'callback_data': f'rep_dismiss_{report[0]}'},
                {'text': '✅ Принять меры', 'callback_data': f'rep_resolve_{report[0]}'}
            ]
        ]
    }
    
    import requests
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={'chat_id': chat_id, 'text': text, 'reply_markup': keyboard}
    )
    
    return {'ok': True}


def show_stats(bot_token: str, chat_id: int, cursor) -> dict:
    """Показать статистику"""
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE status = 'approved'")
    approved = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM matches")
    matches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'pending'")
    reports = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM likes WHERE created_at > NOW() - INTERVAL '24 hours'")
    likes_today = cursor.fetchone()[0]
    
    text = (
        f"📊 Статистика бота:\n\n"
        f"✅ Одобренных анкет: {approved}\n"
        f"⏳ На модерации: {pending}\n"
        f"💜 Совпадений: {matches}\n"
        f"🚩 Активных жалоб: {reports}\n"
        f"❤️ Лайков за 24ч: {likes_today}"
    )
    
    return send_message(bot_token, chat_id, text)


def mod_approve_profile(bot_token: str, chat_id: int, profile_id: int, cursor, message_id: int) -> dict:
    """Модератор одобряет анкету"""
    cursor.execute(
        "UPDATE profiles SET status = 'approved', updated_at = NOW() WHERE id = %s RETURNING telegram_id, name",
        (profile_id,)
    )
    
    result = cursor.fetchone()
    if result:
        user_id, name = result
        send_message(bot_token, user_id, f"✅ Твоя анкета одобрена!\n\nТеперь ты можешь смотреть анкеты командой /browse")
        delete_message(bot_token, chat_id, message_id)
        send_message(bot_token, chat_id, f"✅ Анкета {name} одобрена")
        show_pending_profiles(bot_token, chat_id, cursor)
    
    return {'ok': True}


def mod_reject_profile(bot_token: str, chat_id: int, profile_id: int, cursor, message_id: int) -> dict:
    """Модератор отклоняет анкету"""
    cursor.execute(
        "UPDATE profiles SET status = 'rejected', updated_at = NOW() WHERE id = %s RETURNING telegram_id, name",
        (profile_id,)
    )
    
    result = cursor.fetchone()
    if result:
        user_id, name = result
        send_message(bot_token, user_id, f"❌ Твоя анкета отклонена.\n\nВозможные причины:\n- Неподходящее фото\n- Некорректные данные\n\nСоздай новую анкету командой /create")
        delete_message(bot_token, chat_id, message_id)
        send_message(bot_token, chat_id, f"❌ Анкета {name} отклонена")
        show_pending_profiles(bot_token, chat_id, cursor)
    
    return {'ok': True}


def mod_resolve_report(bot_token: str, chat_id: int, report_id: int, cursor, message_id: int) -> dict:
    """Модератор принимает меры по жалобе"""
    cursor.execute(
        "UPDATE reports SET status = 'resolved' WHERE id = %s",
        (report_id,)
    )
    
    delete_message(bot_token, chat_id, message_id)
    send_message(bot_token, chat_id, f"✅ Жалоба #{report_id} обработана")
    show_reports(bot_token, chat_id, cursor)
    
    return {'ok': True}


def mod_dismiss_report(bot_token: str, chat_id: int, report_id: int, cursor, message_id: int) -> dict:
    """Модератор отклоняет жалобу"""
    cursor.execute(
        "UPDATE reports SET status = 'dismissed' WHERE id = %s",
        (report_id,)
    )
    
    delete_message(bot_token, chat_id, message_id)
    send_message(bot_token, chat_id, f"❌ Жалоба #{report_id} отклонена")
    show_reports(bot_token, chat_id, cursor)
    
    return {'ok': True}


def error_response(message: str) -> dict:
    """Ответ с ошибкой"""
    return {
        'statusCode': 500,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }