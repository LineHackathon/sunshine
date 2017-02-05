#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import re
import requests
import urllib
import os
from flask import Flask, request, abort, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *
from tinydb import TinyDB, Query

import warikan

app = Flask(__name__)

# for LINE Messageing API
f = open('sunshine_bot.json', 'r')
json_dict = json.load(f)
f.close
line_bot_api = LineBotApi(json_dict['token'])
handler = WebhookHandler(json_dict['secret'])
base_url = json_dict['base_url']

# for LINE Login
# auth_url = 'https://068265ed.ngrok.io/auth'
auth_url = base_url + '/auth'
login_channel_id = json_dict['login_channel_id']
login_secret = json_dict['login_secret']

friendsdb = TinyDB('friendsdb.json')
userdb = TinyDB('userdb.json')
warikandb = TinyDB('warikandb.json')

# print(base_url)

def line_login_get_access_token(code):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'grant_type': 'authorization_code',
        'client_id': login_channel_id,
        'client_secret': login_secret,
        'code': code,
        'redirect_uri': auth_url
        }

    r = requests.post(
        'https://api.line.me/v2/oauth/accessToken',
        headers = headers,
        params = payload
    )
    app.logger.info('Auth token: ' + str(r.json()))
    # print payload
    # print r.json()
    # print r.url

    return r.json().get('access_token')

def line_login_get_user_profiles(token):
    headers = {'Authorization': 'Bearer {' + token + '}'}

    r = requests.get(
        'https://api.line.me/v2/profile',
        headers = headers,
    )
    app.logger.info('Auth prof: ' + str(r.json()))
    # print payload
    # print r.json()
    # print r.url

    return r.json().get('userId')

def get_commad_number_str(number):
    return(u'{:,d}'.format(number))

@app.route('/images/<title>/<width>', methods=['GET'])
def images(title, width):
    print(title)
    print(width)
    # 1040, 700, 460, 300, 240
    return send_from_directory(os.path.join(app.root_path, 'static/imagemap', title),
                               str(width) + '.png', mimetype='image/png')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/auth", methods=['GET'])
def auth_callback():
    # https://access.line.me/dialog/oauth/weblogin?response_type=code&client_id=1498580092&redirect_uri=https%3A%2F%2F068265ed.ngrok.io%2Fauth&state=test123
    code = request.args.get('code')
    state = request.args.get('state')

    app.logger.info('Auth args: ' + str(request.args))

    # 認証エラー
    if(code is None):
        print 'Auth error: '
        error = request.args.get('error')
        errorCode = request.args.get('errorCode')
        errorMessage = request.args.get('errorMessage')
        print error
        print errorCode
        print errorMessage
        return 'Auth Error'

    print 'Auth callback: ' + state + ', ' + code

    token = line_login_get_access_token(code)
    uid = line_login_get_user_profiles(token)

    add_user_warikan_group(uid, state)

    return 'Auth OK'

@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    f = open('log.txt','a')
    f.write(json.dumps(json.loads(body)))
    f.write('\n')
    f.close

    body_dict = json.loads(body)

    # handle VERIFY
    if(len(body_dict.get('events')) == 2):
        if(body_dict["events"][0].get('replyToken') == "00000000000000000000000000000000"):
            if(body_dict["events"][1].get('replyToken') == "ffffffffffffffffffffffffffffffff"):
                app.logger.info("VERIFY code received")
                return 'OK'

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def print_error(e):
    print(e.status_code)
    print(e.error.message)
    print(e.error.details)

def print_profile(uid):
    try:
        profile = line_bot_api.get_profile(uid)
        print(profile.display_name)
        print(profile.user_id)
        print(profile.picture_url)
        print(profile.status_message)
        return profile
    except LineBotApiError as e:
        print_error(e)

def get_name(uid):
    add_userdb(uid)
    return userdb.search(Query().id == uid)[0].get('name')

def add_user_warikan_group(uid, wgid):
    for udata in userdb.search(Query().id == uid):
        if(wgid not in udata.get('groups')):
            udata['groups'].append(wgid)
            userdb.update({'groups': udata['groups']}, Query().id == uid)

            line_bot_api.push_message(uid, TextSendMessage(text=wgid + u'に入りました'))
        else:
            line_bot_api.push_message(uid, TextSendMessage(text=u'すでに' + wgid + u'のメンバーだよ'))

    for wdata in warikandb.search(Query().id == wgid):
        if(uid not in wdata.get('users')):
            wdata['users'].append(uid)
            wdata.get('amounts')[uid] = 0
            wdata.get('additional')[uid] = 0
            wdata.get('rates')[uid] = 1.0
            warikandb.update({
                'users': wdata['users'],
                'amounts': wdata['amounts'],
                'additional': wdata['additional'],
                'rates': wdata['rates']},
                Query().id == wgid
            )
            pushid = wgid.split(':',1)[1]
            line_bot_api.push_message(pushid, TextSendMessage(text=get_name(uid) + u'が清算グループに入りました'))

    # print 'user(' + uid + ') is join to gid(' + wgid + ')'
    # print udata[0]
    # print wdata[0]

def get_wgid(source):
    if(source.type == 'group'):
        return 'group:' + source.group_id
    elif(source.type == 'room'):
        return 'room:' + source.room_id

def add_warikan_group(source):
    wgid = get_wgid(source)

    warikandb.insert({'id': wgid, 'name': wgid, 'users': [], 'amounts': {}, 'additional': {}, 'rates': {}})

def del_warikan_group(source):
    wgid = get_wgid(source)

    # グループメンバのデータベース更新
    for wdata in warikandb.search(Query().id == wgid):
        for uid in wdata.get('users'):
            for udata in userdb.search(Query().id == uid):
                if(wgid in udata['groups']):
                    udata['groups'].remove(wgid)
                    userdb.update({'groups': udata['groups']}, Query().id == uid)

    warikandb.remove(Query().id == wgid)

    del_friendsdb(source)

def add_friendsdb(source):
    if(source.type == 'user'):
        if(len(friendsdb.table('users').search(Query().id == source.user_id)) == 0):
            friendsdb.table('users').insert({'id': source.user_id})
        add_userdb(source.user_id)

    elif(source.type == 'group'):
        if(len(friendsdb.table('groups').search(Query().id == source.group_id)) == 0):
            friendsdb.table('groups').insert({'id': source.group_id})

    elif(source.type == 'room'):
        if(len(friendsdb.table('rooms').search(Query().id == source.room_id)) == 0):
            friendsdb.table('rooms').insert({'id': source.room_id})

def del_friendsdb(source):
    if(source.type == 'user'):
        friendsdb.table('users').remove(Query().id == source.user_id)
        del_userdb(source.user_id)
    elif(source.type == 'group'):
        friendsdb.table('groups').remove(Query().id == source.group_id)
    elif(source.type == 'room'):
        friendsdb.table('rooms').remove(Query().id == source.room_id)

def add_userdb(uid):
    if(len(userdb.search(Query().id == uid)) == 0):
        profile = line_bot_api.get_profile(uid)
        userdb.insert({'id': uid, 'name': profile.display_name, 'pict': profile.picture_url, 'status': profile.status_message, 'follow': True, 'groups': []})
    else:
        userdb.update({'follow': True}, Query().id == uid)

def del_userdb(uid):
    if(len(userdb.search(Query().id == uid)) == 0):
        profile = line_bot_api.get_profile(uid)
        userdb.insert({'id': uid, 'name': profile.display_name, 'pict': profile.picture_url, 'status': profile.status_message, 'follow': False, 'groups': []})
    else:
        userdb.update({'follow': False}, Query().id == uid)

def get_template_msg():
    confirm_template_message = TemplateSendMessage(
        alt_text='Confirm Checkout',
        template=ConfirmTemplate(
            text=u'精算を開始しますか？',
            actions=[
                PostbackTemplateAction(
                    label='OK',
                    text='精算をお願いします',
                    data=json.dumps({'cmd': 'start_checkout'})
                ),
                PostbackTemplateAction(
                    label='cancel',
                    text='精算を中止してください',
                    data=json.dumps({'cmd': 'cancel_checkout'})
                ),
            ]
        )
    )
    return confirm_template_message

@handler.default()
def default(event):
    add_friendsdb(event.source)
    print(event)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    add_friendsdb(event.source)

    # テキストを分割
    # http://ymotongpoo.hatenablog.com/entry/20110425/1303724503
    msg_list = re.compile(u"\s+", re.UNICODE).split(event.message.text)
    print msg_list

    if(event.message.text == u'裏メニュー'):
        msg = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                # thumbnail_image_url='https://example.com/image.jpg',
                title=u'裏メニュー',
                text='何する？',
                actions=[
                    PostbackTemplateAction(
                        label='ユーザDB参照',
                        text='user list',
                        data=json.dumps({'cmd': None})
                    ),
                    PostbackTemplateAction(
                        label='友達DB参照',
                        text='friend list',
                        data=json.dumps({'cmd': None})
                    ),
                    PostbackTemplateAction(
                        label='割り勘DB参照',
                        text='warikan list',
                        data=json.dumps({'cmd': None})
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, msg)
        pass

    elif(event.message.text == 'warikan list'):
        group_list = warikandb.all()
        msg = u'現在の割り勘リストは\n'
        for group in group_list:
            msg += 'group: ' + group.get('id') + '\n'
            for user in group.get('users'):
                msg += ' user: ' + get_name(user) + '\n'
                msg += '  amounts: ' + str(group.get('amounts',{}).get(user,'')) + '\n'
                msg += '  additional: ' + str(group.get('additional',{}).get(user,'')) + '\n'
                msg += '  rate: ' + str(group.get('rates',{}).get(user,'')) + '\n'
        msg = msg[:-1]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = msg))
        return
        pass
    elif(event.message.text == 'user list'):
        user_list = userdb.all()
        msg = u'現在のユーザリストは\n'
        for user in user_list:
            msg += 'name: ' + user['name'] + '\n'
            if user.has_key('pict'):
                msg += ' pict: ' + str(user['pict']) + '\n'
            if user.has_key('status'):
                msg += ' status: ' + unicode(user.get('status', '')) + '\n'
        msg = msg[:-1]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = msg))
        return
        pass

    elif(event.message.text == 'friend list'):
        friends_list = friendsdb.all()
        msg = u'現在の友達リストは\n'
        msg += str(friendsdb.table('users').all()) + '\n'
        msg += str(friendsdb.table('groups').all()) + '\n'
        msg += str(friendsdb.table('rooms').all()) + '\n'
        msg = msg[:-1]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = msg))
        return
        pass

    elif(event.message.text == 'seisan'):
        amounts = {
            'A': 9800,
            'B': 7600,
            'C': 7400,
            'D': 17600,
            'E': 0,
            'F': 0,
            'G': 0,
            'H': 0,
            'I': 7,
        }
        transfer_list = warikan.calc_warikan(amounts)
        msg = ''
        for transfer in transfer_list:
            msg += transfer.get('from') + u'⇒' + transfer.get('to') + ': ' + get_commad_number_str(transfer.get('amount')) + u'円\n'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = msg))
        return

    elif(msg_list[0] == u'グループ名'):
        if(len(msg_list) == 1):
            msg = u'現在のグループ名は' + u'未実装'
        else:
            msg = u'新しいグループ名は' + msg_list[1]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = msg))
        return

    elif(msg_list[0] == u'QR'):
        try:
            img_msg = ImageSendMessage(
                original_content_url=u'https://qr-official.line.me/M/lvTHsDPv_o.png',
                preview_image_url=u'https://qr-official.line.me/M/lvTHsDPv_o.png'
            )
            line_bot_api.reply_message(
                event.reply_token,
                img_msg)
        except LineBotApiError as e:
            print_error(e)
        return

    if(event.source.type == 'user'):
        uid = event.source.user_id

        #入力が数字のみの時
        if(event.message.text.isdigit()):
            amount = int(event.message.text)
            msg = get_commad_number_str(amount) + u'円の支払を記録しました\n'

            for udata in userdb.search(Query().id == uid): #ユーザデータ
                for wgid in udata.get('groups'): # 所属するグループ
                    for wdata in warikandb.search(Query().id == wgid): # 割り勘データ
                        wdata.get('amounts')[uid] += amount
                        msg += get_name(uid) + u'さんは合計' + get_commad_number_str(wdata.get('amounts')[uid]) + u'円支払いました'
                        warikandb.update({
                            'amounts': wdata['amounts']},
                            Query().id == wgid
                        )

                        #グループに送信
                        grpmsg = get_name(uid) + u'さんが' + get_commad_number_str(amount) + u'円支払いました'
                        pushid = wgid.split(':',1)[1]
                        line_bot_api.push_message(pushid, TextSendMessage(text = grpmsg))

                        #メンバーに送信
                        pushids = []
                        for member in wdata.get('users'):
                            if(member != uid):
                                pushids.append(member)
                                # line_bot_api.push_message(member, TextSendMessage(text = grpmsg))
                        try:
                            line_bot_api.multicast(pushids, TextSendMessage(text = grpmsg))
                        except LineBotApiError as e:
                            print_error(e)

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text = msg))

        elif(event.message.text == u'支払入力をはじめる'):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=u'みなさんのために何か支払われたのですね。支払われた金額を入力してください'))
            pass

        elif(event.message.text == u'支払内容を確認する'):
            msg = u'現時点の支払内容をご報告します\n'

            for udata in userdb.search(Query().id == uid):
                for wgid in udata.get('groups'):
                    for wdata in warikandb.search(Query().id == wgid):
                        total = 0
                        msg += u'グループID: ' + wdata.get('name') + u'\n'
                        for member in wdata.get('users'):
                            amount = wdata.get('amounts').get(member)
                            msg += get_name(member) + u'さんが' + get_commad_number_str(amount) + u'円支払いました\n'
                            total += amount
                        ave = total / len(wdata.get('users'))
                        msg += u'一人あたり' + get_commad_number_str(ave) + u'円です\n'

            #最後の改行を消す
            msg = msg[:-1]

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=msg))

        elif(event.message.text == u'精算をお願いします'):

            # 所属するグループ全部の清算する問題あり
            for udata in userdb.search(Query().id == uid): #ユーザデータ
                for wgid in udata.get('groups'): #ユーザが所属するグループ
                    msg = ''
                    for wdata in warikandb.search(Query().id == wgid): #グループの割り勘データ
                        # 支払データ作成
                        amounts = wdata.get('amounts')

                        # 割り勘計算
                        transfer_list = warikan.calc_warikan(amounts)

                        # メッセージ作成
                        for transfer in transfer_list:
                            msg += get_name(transfer.get('from')) + u' ⇒ ' + get_name(transfer.get('to')) + ': ' + get_commad_number_str(transfer.get('amount')) + u'円\n'

                        if(msg == ''):
                            msg = '支払はありません'
                        else:
                            #最後の改行を消す
                            msg = u'清算金額をお知らせするね\n' + msg[:-1]

                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = msg))

                    # グループに送信
                    pushid = wgid.split(':',1)[1]
                    line_bot_api.push_message(pushid, TextSendMessage(text = msg))

            # msg = u'一人あたり' + get_commad_number_str(warikan.get_average()) + u'円です'
            # line_bot_api.reply_message(
            #     event.reply_token,
            #     TextSendMessage(text=msg))


        elif(event.message.text == u'ヘルプ'):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=u'申し訳ございません\n準備中です'))

        else:
            pass
        pass

    # group or room
    else:
        if(event.message.text == u'バイバイ'):
            del_warikan_group(event.source)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=u'またね'))
            if(event.source.type == 'group'):
                line_bot_api.leave_group(event.source.group_id)
            elif(event.source.type == 'room'):
                line_bot_api.leave_room(event.source.room_id)

        elif(event.message.text == u'リンク'):
            msg = 'https://line.me/R/ti/p/%40tem1536h'
            img_msg = ImageSendMessage(
                original_content_url='https://qr-official.line.me/M/lvTHsDPv_o.png',
                preview_image_url='https://qr-official.line.me/M/lvTHsDPv_o.png'
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text=msg), img_msg])

        elif(event.message.text == u'ボタン'):
            wgid = get_wgid(event.source)
            imagemap_message = ImagemapSendMessage(
                base_url=base_url + '/images/LINELogin',
                alt_text='LINE Login\nhttps://access.line.me/dialog/oauth/weblogin?response_type=code&client_id=1498580092&redirect_uri=https%3A%2F%2F068265ed.ngrok.io%2Fauth&state=' + wgid,
                base_size=BaseSize(height=302, width=1040),
                actions=[
                    URIImagemapAction(
                        link_uri='https://access.line.me/dialog/oauth/weblogin?response_type=code&client_id=1498580092&redirect_uri=https%3A%2F%2F068265ed.ngrok.io%2Fauth&state=' + wgid,
                        area=ImagemapArea(x=0, y=0, width=1040, height=302)
                    ),
                ]
            )
            line_bot_api.reply_message(
                event.reply_token,
                imagemap_message)

def save_content(message_id, filename):
    message_content = line_bot_api.get_message_content(message_id)
    with open(filename, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    add_friendsdb(event.source)
    # print(event)
    if(event.source.type == 'user'):
        uid = event.source.user_id
        save_content(event.message.id, 'static/' + event.message.id + '.jpg')
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=u'ありがとう\n画像をみんなにシェアするね'))

        # 送信メッセージ
        msgs = [
            TextSendMessage(text=get_name(event.source.user_id) + u'が画像をシェアしてくれたよ'),
            ImageSendMessage(
                original_content_url=base_url + '/static/' + event.message.id + '.jpg',
                preview_image_url=base_url + '/static/' + event.message.id + '.jpg'
            )
        ]
        for udata in userdb.search(Query().id == uid):
            for wgid in udata.get('groups'):
                #グループに送信
                pushid = wgid.split(':',1)[1]
                line_bot_api.push_message(pushid, msgs)

                for wdata in warikandb.search(Query().id == wgid):
                    #メンバーに送信
                    pushids = []
                    for member in wdata.get('users'):
                        if(member != uid):
                            pushids.append(member)
                            # line_bot_api.push_message(member, msgs)
                    line_bot_api.multicast(pushids, msgs)

@handler.add(MessageEvent, message=VideoMessage)
def handle_video_message(event):
    add_friendsdb(event.source)
    pass

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    add_friendsdb(event.source)
    pass

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    add_friendsdb(event.source)
    pass

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    add_friendsdb(event.source)

    msgs = [TextSendMessage(text=u'スタンプを受け取りました')]
    pid = event.message.package_id
    sid = event.message.sticker_id
    wgid = pid + '_' + sid

    # 使えるスタンプのpackage_id
    usable_pid = ["1", "2", "3", "4"]
    if(pid in usable_pid):
        msgs.append(StickerSendMessage(package_id = pid, sticker_id = sid))
    else:
        msgs.append(TextSendMessage(text=u'僕の持っていないスタンプだ\nスタンプIDは{0}だよ'.format(wgid)))

    if(len(warikandb.search(Query().wgid == wgid)) == 0):
        # msgs.append(TextSendMessage(text=u'このスタンプの清算グループはありません'))
        msgs.append(TemplateSendMessage(
            alt_text=u'ConfirmTemplate',
            template=ConfirmTemplate(
                text=u'このスタンプの清算グループはありません\n作りますか？',
                actions=[
                    PostbackTemplateAction(
                        label='はい',
                        text='はい',
                        data=json.dumps({'cmd': 'create_wgid', 'wgid': wgid})
                    ),
                    PostbackTemplateAction(
                        label='いいえ',
                        text='いいえ',
                        data=json.dumps({'cmd': None})
                    ),
                ]
            )
        ))
        # if(event.source.type == 'user'):
        #     uid = event.source.user_id
        #     warikandb.insert({'wgid': wgid, 'name': wgid, 'users': [uid], 'groups': [], 'rooms': [], 'amounts': {uid: 0}, 'additional': {uid: 0}, 'rate': {uid: 1.0}})
        # elif(event.source.type == 'group'):
        #     warikandb.insert({'wgid': wgid, 'name': wgid, 'users': [], 'groups': [event.source.group_id], 'rooms': [], 'amounts': {}, 'additional': {}, 'rate': {}})
        # elif(event.source.type == 'room'):
        #     warikandb.insert({'wgid': wgid, 'name': wgid, 'users': [], 'groups': [], 'rooms': [event.source.room_id], 'amounts': {}, 'additional': {}, 'rate': {}})
    else:
        # msgs.append(TextSendMessage(text=u'このスタンプの清算グループはすでにあります'))
        msgs.append(TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                # thumbnail_image_url='https://example.com/image.jpg',
                # title='Menu',
                text='このスタンプの清算グループはすでにあります',
                actions=[
                    PostbackTemplateAction(
                        label='加入する',
                        text='加入する',
                        data=json.dumps({'cmd': 'join_wgid', 'wgid': wgid})
                    ),
                    PostbackTemplateAction(
                        label='削除する',
                        text='削除する',
                        data=json.dumps({'cmd': 'remove_wgid', 'wgid': wgid})
                    ),
                    PostbackTemplateAction(
                        label='何もしない',
                        text='何もしない',
                        data=json.dumps({'cmd': None})
                    ),
                ]
            )
        ))
        # warikandb.remove(Query().wgid == wgid)

    line_bot_api.reply_message(event.reply_token, msgs)

@handler.add(FollowEvent)
def handle_follow_message(event):
    add_friendsdb(event.source)

    msg = u'はじめまして、Checkunです。友達登録していただきありがとうございます。清算のやり取りをおこなうグループに私を招待して加入ボタンを押してください。'
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg))

@handler.add(UnfollowEvent)
def handle_unfollow_message(event):
    del_friendsdb(event.source)


@handler.add(JoinEvent)
def handle_join_message(event):
    add_friendsdb(event.source)

    wgid = get_wgid(event.source)

    msg1 = \
        u'はじめまして、Checkunです。このグループの会計係をさせていただきます！\n' \
        # u'まずは、このグループメンバー全員の方とお友達になりたいです。\n' \
        # u'次のURLで友達になってね。\n' \
        # u'グループのスタンプを決めて送ってね'
        # u'左のボタンを押して私と友達になって、右のボタンで清算グループに入ってください！'

    # msg2 = 'https://line.me/R/ti/p/%40tem1536h'

    imagemap_message = ImagemapSendMessage(
        base_url=base_url + '/images/LINELogin',
        alt_text='this is an imagemap',
        base_size=BaseSize(height=302, width=1040),
        actions=[
            URIImagemapAction(
                link_uri='https://access.line.me/dialog/oauth/weblogin?response_type=code&client_id=1498580092&redirect_uri=https%3A%2F%2F068265ed.ngrok.io%2Fauth&state=' + wgid,
                area=ImagemapArea(x=0, y=0, width=1040, height=302)
            ),
        ]
    )

    line_bot_api.reply_message(event.reply_token, [
        TextSendMessage(msg1),
        # TextSendMessage(msg2),
        imagemap_message,
    ])

    add_warikan_group(event.source)


@handler.add(LeaveEvent)
def handle_leave_message(event):
    del_warikan_group(event.source)


@handler.add(PostbackEvent)
def handle_postback_event(event):
    add_friendsdb(event.source)

    json_dict = json.loads(event.postback.data)
    print(json_dict)

    # print(event.postback.data)
    # if(event.postback.data == u'start checkout'):
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text=u'精算を始めます'))
    #
    #     start_warikan()
    #
    # elif(event.postback.data == u'cancel checkout'):
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text=u'おっと、焦りは禁物ですよ\n精算を中止します'))
    #     pass


@handler.add(BeaconEvent)
def handle_beacon_event(event):
    add_friendsdb(event.source)
    pass

def start_warikan():
    payment_dict = warikan.calc_warikan()
    print(u'start_warikan')
    print(payment_dict)

    grpmsg = ''
    for uid in payment_dict:
        pmsg = ''
        for pay in payment_dict[uid]:
            grpmsg += get_name(uid) + u'さんは' + get_name(pay) + u'さん'
            pmsg += get_name(pay) + u'さん'
            if(payment_dict[uid][pay] < 0):
                msg = u'に' + get_commad_number_str(-payment_dict[uid][pay]) + '円払ってください\n'
            else:
                msg = u'から' + get_commad_number_str(payment_dict[uid][pay]) + '円受け取ってください\n'
            grpmsg += msg
            pmsg += msg

        line_bot_api.push_message(
            uid,
            TextSendMessage(text=pmsg))
        # print(pmsg)


    if(grpmsg == ''):
        grpmsg = '精算はありません'
    # line_bot_api.push_message(
    #     warikan.group_id,
    #     TextSendMessage(text=grpmsg))
    # print(grpmsg)

    # paypalリンク作成
    # http://944ce050.ngrok.io/vault_sale?amount=xxx
    # https://www.paypal.jp/jp/mms2/service/logos-buttons/images/CO_228_44.png
    # for uid in payment_dict:
    #     for pay in payment_dict[uid]:
    #         if(payment_dict[uid][pay] < 0):
    #             url = 'http://944ce050.ngrok.io/vault_sale?amount=' + str(-payment_dict[uid][pay])
    #             print(url)
    #             line_bot_api.push_message(
    #                 uid,
    #                 TextSendMessage(url))



if __name__ == "__main__":
    app.run(debug=True)
