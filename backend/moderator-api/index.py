import json
import os
import psycopg2
from typing import Optional

def handler(event: dict, context) -> dict:
    """
    API для панели модератора бота знакомств.
    Позволяет одобрять/отклонять анкеты и управлять жалобами.
    """
    method = event.get('httpMethod', 'GET')
    path = event.get('queryStringParameters', {})
    
    if method == 'OPTIONS':
        return cors_response(200, {})
    
    try:
        db_url = os.environ.get('DATABASE_URL')
        schema = os.environ.get('MAIN_DB_SCHEMA', 'public')
        
        if not db_url:
            return cors_response(500, {'error': 'Database not configured'})
        
        conn = psycopg2.connect(db_url, options=f'-c search_path={schema}')
        conn.autocommit = True
        cursor = conn.cursor()
        
        action = path.get('action', '')
        
        if method == 'GET':
            if action == 'pending_profiles':
                result = get_pending_profiles(cursor)
            elif action == 'reports':
                result = get_reports(cursor)
            elif action == 'stats':
                result = get_stats(cursor)
            else:
                result = {'error': 'Unknown action'}
        
        elif method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            if action == 'approve':
                result = approve_profile(cursor, body.get('profile_id'))
            elif action == 'reject':
                result = reject_profile(cursor, body.get('profile_id'))
            elif action == 'resolve_report':
                result = resolve_report(cursor, body.get('report_id'))
            elif action == 'dismiss_report':
                result = dismiss_report(cursor, body.get('report_id'))
            else:
                result = {'error': 'Unknown action'}
        
        else:
            result = {'error': 'Method not allowed'}
        
        cursor.close()
        conn.close()
        
        return cors_response(200, result)
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})


def get_pending_profiles(cursor) -> dict:
    """Получить анкеты на модерации"""
    cursor.execute(
        """SELECT id, telegram_id, username, name, age, city, gender, photo_url, bio, created_at
           FROM profiles 
           WHERE status = 'pending'
           ORDER BY created_at DESC"""
    )
    
    rows = cursor.fetchall()
    profiles = []
    
    for row in rows:
        profiles.append({
            'id': row[0],
            'telegram_id': row[1],
            'username': row[2],
            'name': row[3],
            'age': row[4],
            'city': row[5],
            'gender': row[6],
            'photo_url': row[7],
            'bio': row[8],
            'created_at': row[9].isoformat() if row[9] else None
        })
    
    return {'profiles': profiles}


def get_reports(cursor) -> dict:
    """Получить активные жалобы"""
    cursor.execute(
        """SELECT r.id, r.reporter_id, r.reported_user_id, r.reason, r.status, r.created_at,
                  p1.name as reporter_name, p2.name as reported_name, p2.telegram_id
           FROM reports r
           JOIN profiles p1 ON r.reporter_id = p1.telegram_id
           JOIN profiles p2 ON r.reported_user_id = p2.telegram_id
           WHERE r.status = 'pending'
           ORDER BY r.created_at DESC"""
    )
    
    rows = cursor.fetchall()
    reports = []
    
    for row in rows:
        reports.append({
            'id': row[0],
            'reporter_id': row[1],
            'reported_user_id': row[2],
            'reason': row[3],
            'status': row[4],
            'created_at': row[5].isoformat() if row[5] else None,
            'reporter_name': row[6],
            'reported_name': row[7],
            'reported_telegram_id': row[8]
        })
    
    return {'reports': reports}


def get_stats(cursor) -> dict:
    """Получить статистику бота"""
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE status = 'approved'")
    approved_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE status = 'rejected'")
    rejected_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM matches")
    matches_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'pending'")
    reports_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM likes WHERE created_at > NOW() - INTERVAL '24 hours'")
    likes_today = cursor.fetchone()[0]
    
    return {
        'total_profiles': approved_count + pending_count + rejected_count,
        'approved': approved_count,
        'pending': pending_count,
        'rejected': rejected_count,
        'matches': matches_count,
        'pending_reports': reports_count,
        'likes_today': likes_today
    }


def approve_profile(cursor, profile_id: int) -> dict:
    """Одобрить анкету"""
    if not profile_id:
        return {'error': 'Profile ID required'}
    
    cursor.execute(
        "UPDATE profiles SET status = 'approved', updated_at = NOW() WHERE id = %s RETURNING telegram_id",
        (profile_id,)
    )
    
    result = cursor.fetchone()
    if not result:
        return {'error': 'Profile not found'}
    
    return {'success': True, 'telegram_id': result[0]}


def reject_profile(cursor, profile_id: int) -> dict:
    """Отклонить анкету"""
    if not profile_id:
        return {'error': 'Profile ID required'}
    
    cursor.execute(
        "UPDATE profiles SET status = 'rejected', updated_at = NOW() WHERE id = %s RETURNING telegram_id",
        (profile_id,)
    )
    
    result = cursor.fetchone()
    if not result:
        return {'error': 'Profile not found'}
    
    return {'success': True, 'telegram_id': result[0]}


def resolve_report(cursor, report_id: int) -> dict:
    """Разрешить жалобу (принять меры)"""
    if not report_id:
        return {'error': 'Report ID required'}
    
    cursor.execute(
        "UPDATE reports SET status = 'resolved' WHERE id = %s",
        (report_id,)
    )
    
    return {'success': True}


def dismiss_report(cursor, report_id: int) -> dict:
    """Отклонить жалобу"""
    if not report_id:
        return {'error': 'Report ID required'}
    
    cursor.execute(
        "UPDATE reports SET status = 'dismissed' WHERE id = %s",
        (report_id,)
    )
    
    return {'success': True}


def cors_response(status_code: int, data: dict) -> dict:
    """HTTP ответ с CORS заголовками"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(data, ensure_ascii=False)
    }
