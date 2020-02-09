#! /usr/local/bin/python3
# encoding=utf-8

import datetime
from utils import *

note_require_fields = [
    'avatar', 'nickname', 'school', 'cum_reading', 'post_date',
    'read_duration', 'book_name', 'text_content', 'img_link',
    'like_count', 'favor_count', 'comment_count',
    'nid', 'uid', 'favor_flag', 'like_flag'
]

note_rename_dict = {
    'cum_reading': 'self_cum_reading',
    'nid': 'note.nid',
    'uid': 'note.uid',
    'favor_flag': 'f.nid',
    'like_flag': 'l.nid'
}

note_require_fields_str = get_require_str(note_require_fields, note_rename_dict)

comment_require_fields = [
    'avatar', 'nickname', 'school', 'text_content', 'post_date'
]

comment_rename_dict = {

}

comment_require_str = get_require_str(comment_require_fields, comment_rename_dict)


def get_note_list(page, cursor):
    """
    获取PAGE_SIZE数量的读书笔记，并以对象数组的形式返回
    :param page:    页码
    :param cursor:  句柄
    :return:
    """

    note_select_sql = '''
        SELECT {}
          FROM records.note
          INNER JOIN account.account ON note.uid = account.id
          LEFT JOIN account.account_likes l on note.nid = l.nid and note.uid = l.uid
          LEFT JOIN account.account_favors f on note.nid = f.nid and note.uid = f.uid
          ORDER BY post_date DESC LIMIT %s OFFSET (%s) 
        '''.format(note_require_fields_str)
    cursor.execute(note_select_sql, (PAGE_SIZE, page * PAGE_SIZE,))
    results = cursor.fetchall()

    notes = [{key: value for key, value in zip(note_require_fields, result)} for result in results]

    return notes


def get_self_note_list(uid, page, cursor):
    note_select_sql = '''
        SELECT {}
          FROM records.note
          INNER JOIN account.account ON note.uid = account.id and account.id=%s
          LEFT JOIN account.account_likes l on note.nid = l.nid and note.uid = l.uid
          LEFT JOIN account.account_favors f on note.nid = f.nid and note.uid = f.uid
          ORDER BY post_date DESC LIMIT %s OFFSET (%s) 
        '''.format(note_require_fields_str)

    cursor.execute(note_select_sql, (uid, PAGE_SIZE, page * PAGE_SIZE))
    results = cursor.fetchall()

    notes = [{key: value for key, value in zip(note_require_fields, result)} for result in results]

    return notes


def get_favor_note_list(uid, page, cursor):
    note_select_sql = '''
    SELECT {}
      FROM account.account_favors
      INNER JOIN records.note ON account_favors.nid = note.nid
      INNER JOIN account.account ON note.uid = account.id
      LEFT JOIN account.account_likes l on note.nid = l.nid and note.uid = l.uid
      LEFT JOIN account.account_favors f on note.nid = f.nid and note.uid = f.uid
      WHERE account_favors.uid=%s
      ORDER BY post_date DESC LIMIT %s OFFSET (%s)
    '''.format(note_require_fields_str)

    cursor.execute(note_select_sql, (uid, PAGE_SIZE, page * PAGE_SIZE))
    results = cursor.fetchall()

    notes = [{key: value for key, value in zip(note_require_fields, result)} for result in results]

    return notes


def get_note_content(nid, cursor):
    note_sql = '''
            SELECT {}
              FROM records.note
              INNER JOIN account.account ON note.uid = account.id
              LEFT JOIN account.account_likes l on note.nid = l.nid and note.uid = l.uid
              LEFT JOIN account.account_favors f on note.nid = f.nid and note.uid = f.uid
              where note.nid = (%s)
            '''.format(note_require_fields_str)

    cursor.execute(note_sql, (nid,))
    result = cursor.fetchone()

    note = {key: value for key, value in zip(note_require_fields, result)}

    return note


def get_note_comments(nid, cursor):
    comment_sql = '''
            SELECT {}
                FROM records.comment
                WHERE nid = (%s)
                ORDER BY post_date DESC
        '''.format(comment_require_str)

    cursor.execute(comment_sql, (nid,))
    results = cursor.fetchall()

    comments = [{key: value for key, value in zip(comment_require_fields, result)} for result in results]

    return comments


def send_note(uid, book_name, cur_duration, text_content, img_link, conn, cursor):
    # 先检查今天有没有发过笔记
    yesterday = datetime.datetime.today().date() - datetime.timedelta(days=1)
    today = datetime.datetime.today().date()
    tomorrow = datetime.datetime.today().date() + datetime.timedelta(days=1)
    week_ago = datetime.datetime.today().date() - datetime.timedelta(days=6)
    check_sql = '''SELECT count(*)
            FROM records.note WHERE
            uid = %s and post_date > %s and post_date < %s
        '''
    cursor.execute(check_sql, (uid, today, tomorrow))
    count = cursor.fetchone()[0]

    # 如果有则不能发
    if count > 0:
        return False

    # 若今天还没发过，则可以发。

    # 添加note记录
    insert_sql = '''
            INSERT INTO records.note (uid, book_name, read_duration, text_content, img_link)  
                VALUES (%s, %s, %s, %s, %s)'''
    cursor.execute(insert_sql, (uid, book_name, cur_duration, text_content, img_link))

    # 更新用户信息
    update_sql = '''
            UPDATE account.account SET (self_note_count, self_cum_reading)
            =(self_note_count+1, self_cum_reading+%s) 
            WHERE account.id=%s
            '''
    cursor.execute(update_sql, (cur_duration, uid))

    # 更新连续发帖天数信息
    last_note_sql = '''
        SELECT count(*) FROM records.note
            WHERE uid=%s AND post_date>%s AND post_date<%s
    '''
    cursor.execute(last_note_sql, (uid, yesterday, today))
    yesterday_count = cursor.fetchone()[0]
    # 如果昨天发了贴，则连续天数直接+1。否则连续天数重置为1
    if yesterday_count > 0:
        contious_sql = '''
        UPDATE account.account SET contious_count = contious_count+1 WHERE account.id=%s
        '''
    else:
        contious_sql = '''
        UPDATE account.account SET contious_count = 1 WHERE account.id=%s
        '''
    cursor.execute(contious_sql, (uid,))
    conn.commit()

    # 因为发送了，所以返回成功
    return True


def send_note_test(uid, book_name, cur_duration, text_content, img_link, conn, cursor):
    yesterday = datetime.datetime.today().date() - datetime.timedelta(days=1)
    today = datetime.datetime.today().date()
    tomorrow = datetime.datetime.today().date() + datetime.timedelta(days=1)
    week_ago = datetime.datetime.today().date() - datetime.timedelta(days=6)
    insert_sql = '''
                INSERT INTO records.note (uid, book_name, read_duration, text_content, img_link)  
                    VALUES (%s, %s, %s, %s, %s)'''
    cursor.execute(insert_sql, (uid, book_name, cur_duration, text_content, img_link))

    # 更新用户信息
    update_sql = '''
                UPDATE account.account SET (self_note_count, self_cum_reading)
                =(self_note_count+1, self_cum_reading+%s) 
                WHERE account.id=%s
                '''
    cursor.execute(update_sql, (cur_duration, uid))

    # 更新连续发帖天数信息
    last_note_sql = '''
            SELECT count(*) FROM records.note
                WHERE uid=%s AND post_date>%s AND post_date<%s
        '''
    cursor.execute(last_note_sql, (uid, yesterday, today))
    yesterday_count = cursor.fetchone()[0]
    # 如果昨天发了贴，则连续天数直接+1。否则连续天数重置为1
    if yesterday_count > 0:
        contious_sql = '''
            UPDATE account.account SET contious_count = contious_count+1 WHERE account.id=%s
            '''
    else:
        contious_sql = '''
            UPDATE account.account SET contious_count = 1 WHERE account.id=%s
            '''
    cursor.execute(contious_sql, (uid,))
    conn.commit()

    # 因为发送了，所以返回成功
    return True


def send_comment(uid, nid, comment_content, conn, cursor):
    # 插入评论记录
    insert_sql = '''
        INSERT INTO records.comment (uid, nickname, avatar, nid, text_content, school) 
            SELECT %s, nickname, avatar, %s, %s, school
                FROM account.account 
                WHERE account.id=%s'''
    cursor.execute(insert_sql, (uid, nid, comment_content, uid))

    # 修改笔记下评论数量
    update_sql = '''
        UPDATE records.note SET comment_count=comment_count+1
        WHERE (uid, nid) = (%s, %s)
        '''
    cursor.execute(update_sql, (uid, nid))
    conn.commit()
