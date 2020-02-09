#! /usr/local/bin/python3
# encoding=utf-8

from flask import Flask, jsonify, request, current_app, g, Response
from flask_apscheduler import APScheduler
import psycopg2
import psycopg2.pool
import platform
import account
import record
import toplist

app = Flask(__name__)
scheduler = APScheduler()


def get_pool():
    with app.app_context():
        _pool = current_app.config.get('POOL', None)
    if not _pool:
        with app.app_context():
            print('create pool')
            _pool = current_app.config['POOL'] = psycopg2.pool.ThreadedConnectionPool(5, 100, host='postgres1', user='postgres', port='5432',
                                                                                      password='postgres', dbname='starbook', client_encoding="UTF-8")
    return _pool


@app.before_request
def get_conn():
    _pool = get_pool()
    conn = _pool.getconn()
    g.cur_conn = conn
    g.cur_cursor = conn.cursor()


@app.teardown_request
def put_conn(e):
    _pool = get_pool()
    conn = g.cur_conn
    _pool.putconn(conn)
    g.cur_conn = None
    g.cur_cursor = None
    if e:
        raise TypeError(e)


@app.route('/new')
def hello_world():
    return 'Hello World!'


@app.route('/account/login', methods=['POST', 'GET'])
def qq_login():
    """
    通过qq服务器的jscode获取openid，并尝试获取服务器用户信息
    只有注册用户在服务器有信息，因此若有信息说明已经注册，会一起返回
    若没有信息则说明没有注册，通过account_info为空可以判断
    """
    # 获取 openid
    data = request.get_json()
    jscode = data['code']

    openid, session_key = account.code2session(jscode)

    # 尝试获取account_info
    account_info = account.get_account_info_by_openid(openid, g.cur_cursor)

    return jsonify({'openid': openid, 'account_info': account_info})


@app.route('/account/get_info', methods=['POST'])
def get_info():
    data = request.get_json()
    openid = data['openid']

    # 获取account_info对象
    account_info = account.get_account_info_by_openid(openid, g.cur_cursor)

    return jsonify({'account_info': account_info})


@app.route('/account/add', methods=['POST'])
def add_account():
    data = request.get_json()
    user_info = data['userInfo']
    school, openid = data['school'], data['openid']

    # 添加到数据库
    account.add_account(user_info, openid, school, g.cur_conn, g.cur_cursor)

    # 获取account_info对象
    account_info = account.get_account_info_by_openid(openid, g.cur_cursor)

    return jsonify({'account_info': account_info})


@app.route('/account/like', methods=['POST'])
def change_like_status():
    data = request.get_json()
    action = data['action']
    uid, nid = data['uid'], data['nid']

    # 改变状态
    account.change_note_status('like', action, uid, nid, g.cur_conn, g.cur_cursor)

    return 'success'


@app.route('/account/favor', methods=['POST'])
def change_favor_status():
    data = request.get_json()
    action = data['action']
    uid, nid = data['uid'], data['nid']

    # 改变状态
    account.change_note_status('favor', action, uid, nid, g.cur_conn, g.cur_cursor)

    return 'success'


@app.route('/record/note/list', methods=['POST'])
def get_note_list():
    """获取一组notes"""
    data = request.get_json()
    page = data['page']

    # 获取notes
    notes = record.get_note_list(page, g.cur_cursor)

    return jsonify({'notes': notes})


@app.route('/record/note/self_send', methods=['POST'])
def get_self_note_list():
    """获取该用户发送的notes"""
    data = request.get_json()
    uid = data['uid']
    page = data['page']

    # 获取notes
    notes = record.get_self_note_list(uid, page, g.cur_cursor)

    return jsonify({'notes': notes})


@app.route('/record/note/self_favor', methods=['POST'])
def get_account_favors():
    """获取该用户喜欢的notes"""
    data = request.get_json()
    uid = data['uid']
    page = data['page']

    # 获取notes
    notes = record.get_favor_note_list(uid, page, g.cur_cursor)

    return jsonify({'notes': notes})


@app.route('/record/note/details', methods=['POST'])
def get_note_details():
    """获取note的详细内容及评论内容"""
    data = request.get_json()
    nid = data['noteid']

    note = record.get_note_content(nid, g.cur_cursor)

    comments = record.get_note_comments(nid, g.cur_cursor)

    return jsonify({
        'note': note,
        'comments': comments
    })


@app.route('/records/comment/send', methods=['POST'])
def send_comment():
    """发送评论并重新获取这条笔记的全部评论"""
    data = request.get_json()
    nid, uid = data['nid'], data['uid']
    comment_content = data['cur_comment']

    # 发送评论
    record.send_comment(uid, nid, comment_content, g.cur_conn, g.cur_cursor)

    # 获取最新评论
    comments = record.get_note_comments(nid, g.cur_cursor)

    return jsonify({'comments': comments})


@app.route('/records/note/send', methods=['POST'])
def send_note():
    data = request.get_json()
    uid = data['uid']

    book_name, cur_duration = data['book_name'], data['cur_duration']
    text_content = data['text_content']

    # 是否发送成功
    permission = record.send_note(uid, book_name, cur_duration, text_content, None, g.cur_conn, g.cur_cursor)

    # 如果发送成功，则获取新的account_info
    if permission:
        account_info = account.get_account_info_by_uid(uid, g.cur_cursor)

        return jsonify({
            'permission': 'pass',
            'account_info': account_info
        })
    # 否则返回无权限提示
    else:
        return jsonify({'permission': 'invalid'})


@app.route('/records/note/send_test', methods=['POST'])
def send_note_test():
    data = request.get_json()
    uid = data['uid']

    book_name, cur_duration = data['book_name'], data['cur_duration']
    text_content = data['text_content']

    # 是否发送成功
    permission = record.send_note_test(uid, book_name, cur_duration, text_content, None, g.cur_conn, g.cur_cursor)

    # 如果发送成功，则获取新的account_info
    if permission:
        account_info = account.get_account_info_by_uid(uid, g.cur_cursor)

        return jsonify({
            'permission': 'pass',
            'account_info': account_info
        })
    # 否则返回无权限提示
    else:
        return jsonify({'permission': 'invalid'})


@app.route('/toplist/get_list', methods=['POST', 'GET'])
def get_top_list():
    total_list = toplist.get_total_top_list(g.cur_cursor)
    week_list = toplist.get_week_top_list(g.cur_cursor)
    return jsonify({
        'total_list': total_list,
        'week_list': week_list
    })


@app.route('/img/post_bkg', methods=['POST', 'GET'])
def get_post_bkg():
    with open("static/post_bkg.jpeg", 'rb') as f:
        image = f.read()
    resp = Response(image, mimetype="image/jpeg")
    return resp


def calc_toplist():
    _pool = get_pool()
    conn = _pool.getconn()
    toplist.calc_top_list(conn)
    _pool.putconn(conn)


if __name__ == '__main__':
    pool = None
    try:
        scheduler.add_job(func=calc_toplist, id='calc_toplist', args=(), trigger='interval', seconds=10, replace_existing=True)

        scheduler.init_app(app=app)
        scheduler.start()
        if platform.system() == 'Drawin':  # Mac上说明是测试环境
            app.run()
        else:  # 否则都认为是正式环境
            app.run(host='0.0.0.0', ssl_context=('/ssl_file/www.hyunee.top.pem', '/ssl_file/www.hyunee.top.key'))

    finally:
        pool = current_app.config['POOL']
        if pool:
            pool.closeall()
