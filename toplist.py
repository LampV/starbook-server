#! /usr/local/bin/python3
# encoding=utf-8

import math
from utils import *
import datetime


def calc_top_list(conn):
    print('update toplist')
    today = datetime.datetime.today().date()
    week_ago = datetime.datetime.today().date() - datetime.timedelta(days=6)
    cursor = conn.cursor()

    # 重新计算周读书表
    calc_week_read_sql = '''
    DROP TABlE IF EXISTS toplist.week_reading;
    SELECT note.uid, sum(note.read_duration) as week_cum_reading
    INTO toplist.week_reading
      FROM records.note
      INNER JOIN account.account ON account.id = note.uid
      WHERE note.post_date>%s AND note.post_date<%s
    GROUP BY note.uid
    '''
    cursor.execute(calc_week_read_sql, (week_ago, today))
    conn.commit()
    # 将周读书数据更新到用户表
    update_week_read_sql = '''
    UPDATE account.account SET week_cum_reading=week_reading.week_cum_reading
        FROM toplist.week_reading
        WHERE toplist.week_reading.uid = account.id;
    '''
    cursor.execute(update_week_read_sql)
    conn.commit()


def get_total_top_list(cursor):
    total_require_fields = [
        'uid', 'avatar', 'nickname', 'total_reading', 'school'
    ]
    total_rename_dict = {
        'uid': 'id',
        'total_reading': 'self_cum_reading'
    }
    total_require_str = get_require_str(total_require_fields, total_rename_dict)

    select_total_sql = '''
    SELECT {}
        FROM account.account
    ORDER BY self_cum_reading DESC
    LIMIT (%s)
    '''.format(total_require_str)

    cursor.execute(select_total_sql, (TOP_SIZE, ))
    results = cursor.fetchall()

    top_users = [{key: value for key, value in zip(total_require_fields, result)} for result in results]
    for user in top_users:
        user['read_hour'] = math.ceil(user['total_reading'] / 60)

    return top_users


def get_week_top_list(cursor):
    week_require_fields = [
        'uid', 'avatar', 'nickname', 'week_reading', 'school'
    ]
    week_rename_dict = {
        'uid': 'id',
        'week_reading': 'week_cum_reading'
    }
    week_require_str = get_require_str(week_require_fields, week_rename_dict)

    select_week_sql = '''
    SELECT {}
        FROM account.account
    ORDER BY week_cum_reading DESC
    LIMIT (%s)
    '''.format(week_require_str)

    cursor.execute(select_week_sql, (TOP_SIZE, ))
    results = cursor.fetchall()

    top_users = [{key: value for key, value in zip(week_require_fields, result)} for result in results]
    for user in top_users:
        user['read_hour'] = math.ceil(user['week_reading'] / 60)

    return top_users
