#! /usr/local/bin/python3
# encoding=utf-8

import requests
import json
from utils import *


def code2session(jscode):
    """
    通过qq小程序给出的jscode，换取session信息
    :param jscode:  jscode
    :return: openid, session_ksy
    """
    appid = '1109989884'
    secret = '2VLzNrc73UZ37xVY'
    request_url = 'https://api.q.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code'.format(
        appid, secret, jscode
    )
    res = requests.get(request_url)
    qq_data = json.loads(res.content.decode())
    openid, session_key = qq_data['openid'], qq_data['session_key']
    return openid, session_key


def get_account_info(identify, id_type, cursor):
    """
    通过openid获取用户信息
    :param identify: 用户身份标识
    :param id_type: 标识类型, str in ["openid", "id"]
    :param cursor: 数据库句柄
    :return: dict类型的account_info
    """
    require_fields = [
        'uid', 'nickname', 'avatar', 'school', 'self_cum_reading', 'self_note_count', 'gender', 'contious_count'
    ]
    rename_dict = {
        'uid': 'id'
    }
    require_fields_str = get_require_str(require_fields, rename_dict)

    select_sql = '''
            SELECT {}
              FROM account.account
              WHERE {}=(%s)
            '''.format(require_fields_str, id_type)

    cursor.execute(select_sql, (identify,))
    result = cursor.fetchone()

    # 叫做account_info 是为了和qq的user_info 做区分
    account_info = {key: value for key, value in zip(require_fields, result)} if result else None

    return account_info


def get_account_info_by_openid(openid, cursor):
    """
    通过openid获取用户信息
    :param cursor: 数据库句柄
    :param openid: openid
    :return: dict类型的account_info
    """
    return get_account_info(openid, 'openid', cursor)


def get_account_info_by_uid(uid, cursor):
    """
    uid
    :param cursor: 数据库句柄
    :param uid: uid
    :return: dict类型的account_info
    """
    return get_account_info(uid, 'id', cursor)


def add_account(user_info, openid, school, conn, cursor):
    """
    添加一条account信息
    :param user_info:   QQ用户信息
    :param openid:      用户在小程序的唯一标识
    :param school:      用户学校
    :param conn:        数据库连接
    :param cursor:      连接句柄
    :return:
    """
    insert_sql = '''
        INSERT INTO account.account (openid, nickname, avatar, gender, school) VALUES (%s, %s, %s, %s, %s) 
        '''
    cursor.execute(insert_sql, (openid, user_info['nickName'], user_info['avatarUrl'], user_info['gender'], school))
    conn.commit()
    return 'success'


def change_note_status(status, action, uid, nid, conn, cursor):
    """
    用户对笔记的喜欢/收藏状态改变，需要修改数据库内容，包括：
    1. 在用户和笔记的关系表中增加/删除行
    2. 受到影响的笔记的喜欢数/收藏数会变化
    :param status:  需要改变的状态是：like/favor
    :param action:  具体的动作是 True/False -> 确认或取消
    :param uid:
    :param nid:
    :param conn:
    :param cursor:
    :return:
    """
    # 如果action是True，则执行增加操作
    if action:
        if status == 'like':
            insert_sql = '''INSERT INTO account.account_likes (uid, nid) VALUES (%s, %s)'''
            alter_sql = '''update records.note set like_count=like_count+1 where nid=%s'''
        else:
            insert_sql = '''INSERT INTO account.account_favors (uid, nid) VALUES (%s, %s)'''
            alter_sql = '''update records.note set favor_count=favor_count+1 where nid=%s'''
        cursor.execute(insert_sql, (uid, nid))
        cursor.execute(alter_sql, (nid,))
    # 否则执行删除操作
    else:
        if status == 'like':
            delete_sql = '''DELETE FROM account.account_likes WHERE (uid, nid)=(%s, %s)'''
            alter_sql = '''update records.note set like_count=like_count+1 where nid=%s'''
        else:
            delete_sql = '''DELETE FROM account.account_favors WHERE (uid, nid)=(%s, %s)'''
            alter_sql = '''update records.note set favor_count=favor_count+1 where nid=%s'''
        cursor.execute(delete_sql, (uid, nid))
        cursor.execute(alter_sql, (nid,))

    conn.commit()
    return 'success'
