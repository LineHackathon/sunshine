#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import re
import requests
import urllib
import os
import sys
import traceback

from flask import Flask, request, abort, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *

# import database_mock as db
import datastorage as db
import warikan

app = Flask(__name__)

# 環境変数が見つかればそっちを読む
# 見つからなければjsonファイルを読む
# なければエラー終了
try:
    # 環境変数読み込み
    line_messaging_api_token = os.environ['LINE_MESSAGING_API_TOKEN']
    line_messaging_api_secret = os.environ['LINE_MESSAGING_API_SECRET']
    line_friend_url = os.environ['LINE_FRIEND_URL']
    line_qr_url = os.environ['LINE_QR_URL']
    line_login_channel_id = os.environ['LINE_LOGIN_CHANNEL_ID']
    line_login_secret = os.environ['LINE_LOGIN_SECRET']
    base_url = os.environ['CHECKUN_BASE_URL']
    print('os.envrion')

except:
    try:
        # load from json
        # f = open('checkun_test.json', 'r')
        f = open('checkun_dev.json', 'r')
        json_dict = json.load(f)
        f.close

        line_messaging_api_token = json_dict['LINE_MESSAGING_API_TOKEN']
        line_messaging_api_secret = json_dict['LINE_MESSAGING_API_SECRET']
        line_friend_url = json_dict['LINE_FRIEND_URL']
        line_qr_url = json_dict['LINE_QR_URL']
        line_login_channel_id = json_dict['LINE_LOGIN_CHANNEL_ID']
        line_login_secret = json_dict['LINE_LOGIN_SECRET']
        base_url = json_dict['CHECKUN_BASE_URL']
        print('json')

    except:
        traceback.print_exc()
        print(u'読み込みエラー')
        sys.exit(-1)
print(u'読み込み成功')

# setup LINE Messaging API
line_bot_api = LineBotApi(line_messaging_api_token)
handler = WebhookHandler(line_messaging_api_secret)

# setup LINE Login API
auth_url = base_url + '/auth'

cmd_prefix = u'▶'

# setup database
# db.init('checkundb.json')
udb = {}

# sys.exit(0)

def line_login_get_access_token(code):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'grant_type': 'authorization_code',
        'client_id': line_login_channel_id,
        'client_secret': line_login_secret,
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

    return r.json()

def get_commad_number_str(number):
    return(u'{:,d}'.format(number))

@app.route('/images/<title>/<width>', methods=['GET'])
def images(title, width):
    # print(title)
    # print(width)
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
    profile = line_login_get_user_profiles(token)
    uid = profile.get("userId")
    name = profile.get("displayName")

    # add_user_warikan_group(uid, state)
    db.add_user_to_group(uid, state)
    msgs = []
    msgs.append(TextSendMessage(text = u'{}さんが清算グループに入りました'.format(name)))
    line_bot_api.push_message(state, msgs)

    return 'Auth OK'

@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    f = open('log.txt','a')
    f.write(json.dumps(json.loads(body), indent=2, sort_keys=True, separators=(',', ': ')))
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

@handler.default()
def default(event):
    pass

def get_commad_number_str(number):
    return(u'{:,d}'.format(number))

def get_id(source):
    if source.type == 'user':
        return source.user_id
    elif source.type == 'group':
        return source.group_id
    elif source.type == 'room':
        return source.room_id

def get_name(uid):
    return line_bot_api.get_profile(uid).display_name

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if event.source.type == 'user':
        print get_name(event.source.user_id)

    id = get_id(event.source)
    reply_msgs = []
    #コマンド受信
    if(event.message.text[0] == cmd_prefix):
        print('command received')
        cmd = event.message.text[1:]

        if cmd == u'支払登録':
            reply_msgs.append(TextSendMessage(text = u'何か支払ったんだね'))
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払登録ボタン',
                template=ButtonsTemplate(
                    # thumbnail_image_url='https://example.com/image.jpg',
                    title=u'支払登録',
                    text=u'リストから選んでね',
                    actions=[
                        # PostbackTemplateAction(
                        MessageTemplateAction(
                            label=u'金額入力で登録',
                            text=cmd_prefix + u'支払登録（金額入力）',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                            label=u'電卓入力で登録',
                            text=cmd_prefix + u'支払登録（電卓入力）',
                            # data='action=buy&itemid=1'
                        ),
                        # PostbackTemplateAction(
                        MessageTemplateAction(
                            label=u'レシートで登録',
                            text=cmd_prefix + u'支払登録（レシート）',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'支払登録（金額入力）':
            udb[id] = {'status': 'input_amount'}
            reply_msgs.append(TextSendMessage(text = u'金額を入力してね(1~999,999)'))
        elif cmd == u'支払登録（電卓入力）':
            udb[id] = {}
            udb[id]['amount'] = 0

            actions=[]
            calc_buttonid = ['7', '8', '9', 'C', '4', '5', '6', 'C', '1', '2', '3', 'E', '0', '00', '000', 'E']
            button_size = 260
            for y in range(4):
                for x in range(4):
                    actions.append(MessageImagemapAction(text=cmd_prefix + u'電卓' + calc_buttonid[x+y*4], area=ImagemapArea(x=x*button_size, y=y*button_size, width=button_size, height=button_size)))

            reply_msgs.append(ImagemapSendMessage(
                base_url=base_url + '/images/CalcButtonT',
                alt_text='電卓入力ボタン',
                base_size=BaseSize(height=1040, width=1040),
                actions=actions
            ))
        elif cmd[0:2] == u'電卓':
            if len(cmd[2:]) == 1:
                if cmd[2] == 'E':
                    pass
                elif cmd[2] == 'C':
                    udb[id]['amount'] = 0
                else:
                    n = int(cmd[2])
                    udb[id]['amount'] = udb[id]['amount'] * 10 + n

            elif len(cmd[2:]) == 2:
                udb[id]['amount'] = udb[id]['amount'] * 100
            elif len(cmd[2:]) == 3:
                udb[id]['amount'] = udb[id]['amount'] * 1000

            actions=[]
            calc_buttonid = ['7', '8', '9', 'C', '4', '5', '6', 'C', '1', '2', '3', 'E', '0', '00', '000', 'E']
            button_size = 260
            for y in range(4):
                for x in range(4):
                    actions.append(MessageImagemapAction(text=cmd_prefix + u'電卓' + calc_buttonid[x+y*4], area=ImagemapArea(x=x*button_size, y=y*button_size, width=button_size, height=button_size)))

            if cmd[2] == 'E':
                udb[id]['status'] = 'input_use'
                reply_msgs.append(TextSendMessage(text = u'{amount}円だね\n何の金額か教えて(ex.レンタカー代)'.format(amount=get_commad_number_str(udb[id]['amount']))))
            else:
                reply_msgs.append(ImagemapSendMessage(
                    base_url=base_url + '/images/CalcButtonT',
                    alt_text='電卓入力ボタン',
                    base_size=BaseSize(height=1040, width=1040),
                    actions=actions
                ))
                reply_msgs.append(TextSendMessage(text = u'{amount}円 これで良ければEnterボタンを押してね'.format(amount=get_commad_number_str(udb[id]['amount']))))

        elif cmd == u'支払登録（レシート）':
            udb[id] = {'status': 'input_amount'}
            # reply_msgs.append(TextSendMessage(text = u'レシートを撮るか、写真を選択してね'))
            reply_msgs.append(TextSendMessage(text = u'まだ実装していません'))
        elif cmd == u'確認':
            # reply_msgs.append(TextSendMessage(text = u'何の確認をするかリストから選んでね'))
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'確認ボタン',
                template=ButtonsTemplate(
                    # thumbnail_image_url='https://example.com/image.jpg',
                    title=u'確認',
                    text=u'何の確認をするかリストから選んでね',
                    actions=[
                        # PostbackTemplateAction(
                        MessageTemplateAction(
                            label=u'支払メンバー確認',
                            text=cmd_prefix + u'支払メンバー確認',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                            label=u'個別支払合計',
                            text=cmd_prefix + u'個別支払合計',
                            # data='action=buy&itemid=1'
                        ),
                        # PostbackTemplateAction(
                        MessageTemplateAction(
                            label=u'支払一覧',
                            text=cmd_prefix + u'支払一覧',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'支払メンバー確認':
            groups = db.get_user_groups(event.source.user_id)
            for gid in groups:
                users = db.get_group_users(gid)
                text = u'現在この精算グループには{}人の方が対象になっています\n'.format(len(users))
                for uid in users:
                    text += (get_name(uid)) + u'さん\n'

            if len(text):
                text = text[:-1]
                reply_msgs.append(TextSendMessage(text = text))

        elif cmd == u'個別支払合計':
            text = u'現時点の各個人の支払い合計を報告します。\n'
            groups = db.get_user_groups(event.source.user_id)
            for gid in groups:
                if len(groups) > 1:
                    text += u'グループ：{}'.format(db.get_group_info(gid).get("name"))
                payments = db.get_groups_payments(gid)
                totals = {}
                for payment in payments:
                    uid = payment["payment_uid"]
                    amount = payment["amount"]
                    totals[uid] = totals.get(uid,0) + amount

                total = 0
                for k, v in totals.items():
                    text += u'{}さんが{}円支払いました\n'.format(get_name(k), v)
                    total += v

                users = db.get_group_users(gid)
                text += u'{}人だと、一人あたり{}円です'.format(len(users), total/len(users))

            reply_msgs.append(TextSendMessage(text = text))
        elif cmd == u'支払一覧':
            text = u'現時点の各個人の支払い合計を報告します。\n'
            groups = db.get_user_groups(event.source.user_id)
            for gid in groups:
                if len(groups) > 1:
                    text += u'グループ：{}'.format(db.get_group_info(gid).get("name"))
                payments = db.get_groups_payments(gid)
                totals = {}
                for payment in payments:
                    uid = payment["payment_uid"]
                    amount = payment["amount"]
                    text += u'{}さんが{}円支払いました\n'.format(get_name(uid), amount)

            reply_msgs.append(TextSendMessage(text = text))
            # uid = event.source.user_id
            # payments = db.get_user_groups_payments(uid)
            # for payment in payments:
            #     pass
            # reply_msgs.append(TemplateSendMessage(
            #     alt_text='支払一覧',
            #     template=ButtonsTemplate(
            #         # thumbnail_image_url=udb[id].get('image_url', None),
            #         title=u'支払一覧',
            #         text = u'リストの登録金額を選択すると詳細を表示するよ。表示は新しいものから表示しています。',
            #         actions=[
            #             MessageTemplateAction(
            #             # PostbackTemplateAction(
            #                 label=u'『支払金額』(『支払対象人数』)',
            #                 text=cmd_prefix + u'『支払金額』(『支払対象人数』)',
            #                 # data='action=buy&itemid=1'
            #             ),
            #             MessageTemplateAction(
            #             # PostbackTemplateAction(
            #                 label=u'『支払金額』(『支払対象人数』)',
            #                 text=cmd_prefix + u'『支払金額』(『支払対象人数』)',
            #                 # data='action=buy&itemid=1'
            #             ),
            #             MessageTemplateAction(
            #             # PostbackTemplateAction(
            #                 label=u'『支払金額』(『支払対象人数』)',
            #                 text=cmd_prefix + u'『支払金額』(『支払対象人数』)',
            #                 # data='action=buy&itemid=1'
            #             ),
            #             MessageTemplateAction(
            #             # PostbackTemplateAction(
            #                 label=u'『支払金額』(『支払対象人数』)',
            #                 text=cmd_prefix + u'『支払金額』(『支払対象人数』)',
            #                 # data='action=buy&itemid=1'
            #             ),
            #         ]
            #     )
            # ))
        elif cmd == u'『支払金額』(『支払対象人数』)':
            text = u'''『対象ユーザ』さんが『項目名』で『支払金額』円支払
いました。
この支払いに対する支払対象者は『支払対象人数』名で
す。
『対象ユーザ』さん
『対象ユーザ』さん
・
・
・
『対象ユーザ』さん
『対象ユーザ』さん
会計係さん'''
            reply_msgs.append(TextSendMessage(text = text))
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払一覧ボタン',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'支払一覧',
                    text = u'リストの登録金額を選択すると詳細を表示するよ。表示は新しいものから表示しています。',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'何もしない',
                            text=cmd_prefix + u'何もしない',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'支払対象変更',
                            text=cmd_prefix + u'支払対象変更',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'内容訂正',
                            text=cmd_prefix + u'内容訂正',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'支払削除',
                            text=cmd_prefix + u'支払削除',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'何もしない':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'何もしないボタン',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'支払一覧に戻りますか?',
                    text=u'支払一覧に戻りますか?',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'戻る',
                            text=cmd_prefix + u'支払一覧',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'終了する',
                            text=cmd_prefix + u'終了する',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'終了する':
            reply_msgs.append(TextSendMessage(text = u'支払一覧確認を終了しました'))

        elif cmd == u'支払対象変更':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払対象変更ボタン',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'支払対象変更?',
                    text = u'行いたい操作をリストから選んでください。',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'1名だけにする',
                            text=cmd_prefix + u'1名だけにする',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'1名減らす',
                            text=cmd_prefix + u'1名減らす',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'1名増やす',
                            text=cmd_prefix + u'1名増やす',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'全員対象にする',
                            text=cmd_prefix + u'全員対象にする',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'1名だけにする':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'1名だけにするボタン',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'特定支払',
                    text = u'支払対象となるユーザーをリストから選んでください。',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'特定支払『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'特定支払『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'特定支払『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'キャンセル',
                            text=cmd_prefix + u'キャンセル',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'特定支払『対象ユーザ』さん':
            # db.set_debt_uid_list(gid, uid_list)
            db.set_debt_uid_list('sample_gid', ['sample_user'])
            reply_msgs.append(TextSendMessage(text = u'支払対象者を『対象ユーザ』さんに設定しました'))
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払一覧に戻りますか?',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'支払一覧に戻りますか?',
                    text = u'支払一覧に戻りますか?',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'戻る',
                            text=cmd_prefix + u'支払一覧',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'終了する',
                            text=cmd_prefix + u'終了する',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'1名減らす':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払対象除外',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'支払対象除外',
                    text = u'支払対象から除外するユーザーをリストから選んでください。',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'キャンセル',
                            text=cmd_prefix + u'キャンセル',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'1名増やす':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払対象追加',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'支払対象追加',
                    text = u'支払対象に追加するユーザーをリストから選んでください',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'キャンセル',
                            text=cmd_prefix + u'キャンセル',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'全員対象にする':
            reply_msgs.append(TextSendMessage(text = u'全てのユーザを支払対象に設定しました'))
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払一覧に戻りますか?',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'支払一覧に戻りますか?',
                    text = u'支払一覧に戻りますか?',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'戻る',
                            text=cmd_prefix + u'支払一覧',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'終了する',
                            text=cmd_prefix + u'終了する',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))

        elif cmd == u'内容訂正':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払訂正ボタン',
                template=ButtonsTemplate(
                    # thumbnail_image_url='https://example.com/image.jpg',
                    title=u'支払訂正',
                    text=u'訂正する項目をリストから選んでね',
                    actions=[
                        # PostbackTemplateAction(
                        MessageTemplateAction(
                            label=u'金額',
                            text=cmd_prefix + u'支払訂正金額',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                            label=u'支払項目',
                            text=cmd_prefix + u'支払訂正項目',
                            # data='action=buy&itemid=1'
                        ),
                        # PostbackTemplateAction(
                        MessageTemplateAction(
                            label=u'写真',
                            text=cmd_prefix + u'支払訂正写真',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'支払削除':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払削除ボタン',
                template=ButtonsTemplate(
                    # thumbnail_image_url='https://example.com/image.jpg',
                    # title=u'支払削除',
                    text=u'この支払を削除してもよいですか？',
                    actions=[
                        # PostbackTemplateAction(
                        MessageTemplateAction(
                            label=u'削除',
                            text=cmd_prefix + u'支払削除実行',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                            label=u'中止',
                            text=cmd_prefix + u'中止',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'支払削除実行':
            # db.delete_payment(payment_id)
            reply_msgs.append(TextSendMessage(text = u'支払を削除しました'))
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払一覧に戻りますか?',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'支払一覧に戻りますか?',
                    text = u'支払一覧に戻りますか?',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'戻る',
                            text=cmd_prefix + u'支払一覧',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'終了する',
                            text=cmd_prefix + u'終了する',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'中止':
            reply_msgs.append(TextSendMessage(text = u'削除操作を中止しました'))
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'支払一覧に戻りますか?',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'支払一覧に戻りますか?',
                    text = u'支払一覧に戻りますか?',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'戻る',
                            text=cmd_prefix + u'支払一覧',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'終了する',
                            text=cmd_prefix + u'終了する',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'支払訂正金額':
            # db.update_payment(amount, description, image)
            db.update_payment(amout = 1000)
            reply_msgs.append(TextSendMessage(text = u'省略'))
        elif cmd == u'支払訂正項目':
            db.update_payment(description = 'テスト')
            reply_msgs.append(TextSendMessage(text = u'省略'))
        elif cmd == u'支払訂正写真':
            db.update_payment(image = 'https://example.com/image')
            reply_msgs.append(TextSendMessage(text = u'省略'))
        elif cmd == u'清算':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'清算',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'清算',
                    text = u'何の処理をするかリストから選んでね',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'精算実行・更新',
                            text=cmd_prefix + u'精算実行・更新',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'精算報告',
                            text=cmd_prefix + u'精算報告',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'精算結果確認',
                            text=cmd_prefix + u'精算結果確認',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'精算実行・更新':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'精算実行・更新',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'精算実行・更新',
                    text = u'新しい精算を開始します。よろしいですか?以前に実行した精算情報は全て消えてしまいます。',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'実行する',
                            text=cmd_prefix + u'精算実行・更新実行',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'中止する',
                            text=cmd_prefix + u'精算実行・更新中止',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'精算実行・更新実行':
            text = u''
            uid = event.source.user_id
            groups = db.get_user_groups(uid)
            for gid in groups:
                if len(groups) > 1:
                    text += u'グループ：{}'.format(db.get_group_info(gid).get("name"))
                payments = db.get_groups_payments(gid)
                totals = {}
                for payment in payments:
                    uid = payment["payment_uid"]
                    amount = payment["amount"]
                    totals[uid] = totals.get(uid,0) + amount

                users = db.get_group_users(gid)

                transfer_text = u''
                transfer_list = warikan.calc_warikan2(users, totals)
                for transfer in transfer_list:
                    transfer_text += u'{}さんは{}さんに{}円支払ってください\n'.format(get_name(transfer["from"]), get_name(transfer["to"]), transfer["amount"])
                    pay_text = u'{}さんに{}円支払ってください\n'.format(get_name(transfer["to"]), transfer["amount"])
                    rec_text = u'{}さんから{}円受け取ってください\n'.format(get_name(transfer["from"]), transfer["amount"])
                    print pay_text
                    print rec_text
                    print transfer["from"]
                    if transfer["from"] == uid:
                        text += pay_text
                    else:
                        # line_bot_api.push_message(transfer["from"], TextSendMessage(text = push_text))
                        pass
                    if transfer["to"] == uid:
                        text += rec_text
                    else:
                        pass


                line_bot_api.push_message(gid, TextSendMessage(text = transfer_text))

            if len(text):
                reply_msgs.append(TextSendMessage(text = text))

#             text = u''
#
#             reply_msgs.append(TextSendMessage(text = u'精算結果をグループラインに投稿しました'))
#             reply_msgs.append(TextSendMessage(text = u'''精算結果をお知らせします
# 『対象ユーザ』さんに『未精算金額』円払ってください or『対象ユーザ』さんに『未精算金額』円もらってくだ さい
# 支払が完了したら精算報告をしてください or 受取が完了したら精算報告をしてください'''))
            # ここでグループに投稿

        elif cmd == u'精算実行・更新中止':
            reply_msgs.append(TextSendMessage(text = u'精算処理を中止しました'))

        elif cmd == u'精算報告':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'精算報告',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'精算報告',
                    text = u'『対象ユーザ』さんに『未精算金額』円払払いました か? or『対象ユーザ』さんに『未精算金額』円もらいました',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'完了した',
                            text=cmd_prefix + u'精算完了',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'まだしてない',
                            text=cmd_prefix + u'精算まだ',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))

        elif cmd == u'精算完了':
            reply_msgs.append(TextSendMessage(text = u'ありがとうございます!『対象ユーザ』さんに確認します!'))
            reply_msgs.append(TextSendMessage(text = u'『対象ユーザ』さんに確認しました!あなたの精算は完了です！ or 『対象ユーザ』さんの確認が取れませんでした。再度精算をしてから報告してください。'))
        elif cmd == u'精算まだ':
            reply_msgs.append(TextSendMessage(text = u'早く払ってください!! or 早くもらってください!!'))

        elif cmd == u'精算結果確認':
            reply_msgs.append(TextSendMessage(text = u'''現在の精算結果をお知らせします
【精算済】『対象ユーザ』さん →『対象ユーザ』さ
ん:『未精算金額』円
『対象ユーザ』さん →『対象ユーザ』さん:『未精算
金額』円
・
・
・
【精算済】『対象ユーザ』さん →『対象ユーザ』さ
ん:『未精算金額』円'''))

        elif cmd == u'設定':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'設定',
                template=CarouselTemplate(
                    columns=[
                        CarouselColumn(
                            # thumbnail_image_url=base_url + '/static/car.jpg',
                            title=u'精算設定',
                            text=u'どれを操作するかリストから選んでね',
                            actions=[
                                MessageTemplateAction(
                                    label=u'丸め設定',
                                    text=cmd_prefix + u'丸め設定'
                                ),
                                MessageTemplateAction(
                                    label=u'傾斜設定',
                                    text=cmd_prefix + u'傾斜設定'
                                ),
                                MessageTemplateAction(
                                    label=u'精算設定確認',
                                    text=cmd_prefix + u'精算設定確認'
                                ),
                            ]
                        ),
                        CarouselColumn(
                            # thumbnail_image_url=base_url + '/static/car.jpg',
                            title=u'全般',
                            text=u'どれを操作するかリストから選んでね',
                            actions=[
                                MessageTemplateAction(
                                    label=u'会計係の設定',
                                    text=cmd_prefix + u'会計係の設定'
                                ),
                                MessageTemplateAction(
                                    label=u'初期化',
                                    text=cmd_prefix + u'初期化'
                                ),
                                MessageTemplateAction(
                                    label=u'改善要望・バグ報告',
                                    text=cmd_prefix + u'改善要望・バグ報告'
                                ),
                            ]
                        ),

                    ]
                )
            ))

        elif cmd == u'丸め設定':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'丸め設定',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'丸め設定',
                    text = u'端数の丸め設定値を選択してください。',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'設定しない',
                            text=cmd_prefix + u'丸め1',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'100円',
                            text=cmd_prefix + u'丸め100',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'500円',
                            text=cmd_prefix + u'丸め500',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'1,000円',
                            text=cmd_prefix + u'丸め1000',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'丸め1':
            reply_msgs.append(TextSendMessage(text = u'端数の丸め設定はしていません'))
        elif cmd == u'丸め100':
            reply_msgs.append(TextSendMessage(text = u'丸め設定値を100円にしました'))
        elif cmd == u'丸め500':
            reply_msgs.append(TextSendMessage(text = u'丸め設定値を500円にしました'))
        elif cmd == u'丸め1000':
            reply_msgs.append(TextSendMessage(text = u'丸め設定値を1,000円にしました'))

        elif cmd == u'傾斜設定':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'傾斜種類選択',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'傾斜種類選択',
                    text = u'設定をしたい傾斜の種類を選択してください',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'傾斜割合',
                            text=cmd_prefix + u'傾斜割合',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'傾斜額',
                            text=cmd_prefix + u'傾斜額',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'傾斜設定確認',
                            text=cmd_prefix + u'傾斜設定確認',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        # elif cmd == u'傾斜割合':

        elif cmd in [u'傾斜割合', u'傾斜額']:
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'傾斜対象選択',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'傾斜対象選択',
                    text = u'傾斜設定をしたいユーザーを選択してください',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'全ユーザー初期化',
                            text=cmd_prefix + u'全ユーザー初期化',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'傾斜設定『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'傾斜設定『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'『対象ユーザ』さん',
                            text=cmd_prefix + u'傾斜設定『対象ユーザ』さん',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'全ユーザー初期化':
            reply_msgs.append(TextSendMessage(text = u'全てのユーザーの傾斜(割合 or 額)をリセットしました'))

        elif cmd == u'傾斜設定『対象ユーザ』さん':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'傾斜割合設定',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    title=u'傾斜割合設定',
                    text = u'対象ユーザーの傾斜割合を設定してください',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'x 0.8',
                            text=cmd_prefix + u'傾斜割合設定x0.8',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'x 1.0',
                            text=cmd_prefix + u'傾斜割合設定x1.0',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'x 1.2',
                            text=cmd_prefix + u'傾斜割合設定x1.2',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'その他',
                            text=cmd_prefix + u'傾斜割合設定 その他',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'傾斜割合設定x0.8':
            reply_msgs.append(TextSendMessage(text = u'『対象ユーザ』さんの傾斜割合を0.8に設定しました'))
        elif cmd == u'傾斜割合設定x1.0':
            reply_msgs.append(TextSendMessage(text = u'『対象ユーザ』さんの傾斜割合を1.0に設定しました'))
        elif cmd == u'傾斜割合設定x1.2':
            reply_msgs.append(TextSendMessage(text = u'『対象ユーザ』さんの傾斜割合を1.2に設定しました'))
        elif cmd == u'傾斜割合設定 その他':
            reply_msgs.append(TextSendMessage(text = u'希望の割合を入力してください（ex. 1.5、0.7）'))
            udb[id]['status'] = 'set_rate'

        elif cmd == u'傾斜設定確認':
            reply_msgs.append(TextSendMessage(text = u'''傾斜設定は以下のようになっています
『対象ユーザ』さんに傾斜はありません
『対象ユーザ』さんには+2,000円の傾斜があります
・
・
・
『対象ユーザ』さんには×0.8、-1,000円の傾斜があります'''))

        elif cmd == u'精算設定確認':
            reply_msgs.append(TextSendMessage(text = u'''精算設定は以下のようになっています

丸め設定：『500』円

『対象ユーザ』さんに傾斜はありません
『対象ユーザ』さんには+2,000円の傾斜があります
・
・
・
『対象ユーザ』さんには×0.8、-1,000円の傾斜があります'''))


        elif cmd == u'会計係の設定':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'会計係の設定',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'会計係の設定',
                    text = u'企業や団体の経費立替係を入れる場合に設定します。',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'設定する',
                            text=cmd_prefix + u'会計係設定する',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'設定しない',
                            text=cmd_prefix + u'会計係設定しない',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'会計係設定する':
            reply_msgs.append(TextSendMessage(text = u'会計係設定しました'))
        elif cmd == u'会計係設定しない':
            reply_msgs.append(TextSendMessage(text = u'会計係設定を解除しました'))

        elif cmd == u'初期化':
            reply_msgs.append(TemplateSendMessage(
                alt_text=u'初期化',
                template=ButtonsTemplate(
                    # thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'初期化',
                    text = u'全ての設定を初期化します。よろしいですか？',
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'はい',
                            text=cmd_prefix + u'初期化する',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'いいえ',
                            text=cmd_prefix + u'初期化しない',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
        elif cmd == u'初期化する':
            reply_msgs.append(TextSendMessage(text = u'初期化しました'))
        elif cmd == u'初期化しない':
            reply_msgs.append(TextSendMessage(text = u'初期化を中止しました'))

        elif cmd == u'改善要望・バグ報告':
            reply_msgs.append(TextSendMessage(text = u'''以下のリンクからお問い合わせください

（ヘルプとかのホームページリンク）
http://www.checkun.com/'''))


        elif cmd == u'ヘルプ':
            reply_msgs.append(TextSendMessage(text = u'知りたいことを選んでね'))
        else:
            reply_msgs.append(TextSendMessage(text = u'知らないコマンドだ'))

    else:
        try:
            status = udb[id]['status']
        except:
            status = 'none'
        print status

        if status == 'input_amount':
            if event.message.text.isdigit():
                amount = int(event.message.text)
                if (amount < 1) | (amount > 999999):
                    reply_msgs.append(TextSendMessage(text = u'入力できるのは1〜999,999円だよ'))

                else:
                    udb[id]['status'] = 'input_use'
                    udb[id]['amount'] = amount
                    reply_msgs.append(TextSendMessage(text = u'何の金額か教えて(ex.レンタカー代)'))

            else:
                reply_msgs.append(TextSendMessage(text = u'入力できるのは1〜999,999円だよ'))

        elif status == 'input_use':
            udb[id]['use'] = event.message.text
            reply_msgs.append(TemplateSendMessage(
                alt_text='登録確認',
                template=ButtonsTemplate(
                    thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'登録確認',
                    text = u'{use}で{amount}円、これで登録してよいですか？'.format(use = udb[id]['use'], amount = get_commad_number_str(udb[id]['amount'])),
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'OK',
                            text=u'OK',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'訂正する',
                            text=u'訂正する',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
            udb[id]['status'] = 'ask_photo_addition'

        elif status == 'ask_photo_addition':
            if event.message.text == u'OK':
                reply_msgs.append(TemplateSendMessage(
                    alt_text='写真確認',
                    template=ConfirmTemplate(
                        text = u'この支払に対して一緒に写真も登録しますか？',
                        actions=[
                            MessageTemplateAction(
                            # PostbackTemplateAction(
                                label=u'はい',
                                text=u'はい',
                                # data='action=buy&itemid=1'
                            ),
                            MessageTemplateAction(
                            # PostbackTemplateAction(
                                label=u'いいえ',
                                text=u'いいえ',
                                # data='action=buy&itemid=1'
                            ),
                        ]
                    )
                ))
                udb[id]['status'] = 'confirm_photo_addition'

            elif event.message.text == u'訂正する':
                reply_msgs.append(TemplateSendMessage(
                    alt_text=u'支払訂正ボタン',
                    template=ButtonsTemplate(
                        # thumbnail_image_url='https://example.com/image.jpg',
                        title=u'支払訂正',
                        text=u'訂正する項目をリストから選んでね',
                        actions=[
                            # PostbackTemplateAction(
                            MessageTemplateAction(
                                label=u'金額',
                                text=u'金額',
                                # data='action=buy&itemid=1'
                            ),
                            MessageTemplateAction(
                                label=u'支払項目',
                                text=u'支払項目',
                                # data='action=buy&itemid=1'
                            ),
                            # PostbackTemplateAction(
                            MessageTemplateAction(
                                label=u'写真',
                                text=u'写真',
                                # data='action=buy&itemid=1'
                            ),
                        ]
                    )
                ))
                udb[id]['status'] = 'modify_payment'

            else: #訂正する
                reply_msgs.append(TextSendMessage(text = u'ボタンで選んでね'))

        elif status == 'confirm_photo_addition':
            if event.message.text == u'はい':
                reply_msgs.append(TextSendMessage(text = u'写真を撮るか、写真を選択してね'))
                udb[id]['status'] = 'add_photo'

            elif event.message.text == u'いいえ':
                reply_msgs.append(TextSendMessage(text = u'登録完了しました！この内容でみんなに報告しますね！'))
                # ここでDB登録＆みんなに報告
                groups = db.get_user_groups(id)
                for gid in groups:
                    db.add_payment(gid, id, udb[id]["amount"], udb[id].get("use"), udb[id].get("image"))

                    msgs = []
                    name = get_name(id)
                    if "use" in udb[id]:
                        msgs.append(TextSendMessage(text = u'{}さんが{}に{}円支払いました'.format(name, udb[id].get("use"), udb[id]["amount"])))
                    else:
                        msgs.append(TextSendMessage(text = u'{}さんが{}円支払いました'.format(name, udb[id]["amount"])))
                    if "image" in udb[id]:
                        msgs.append(ImageSendMessage(original_content_url = udb[id]["image"], preview_image_url = udb[id]["image"]))
                    line_bot_api.push_message(gid, msgs)

                del udb[id]
            else:
                reply_msgs.append(TextSendMessage(text = u'ボタンで選んでね'))

        elif status == 'modify_payment':
            if event.message.text == u'金額':
                reply_msgs.append(TextSendMessage(text = u'金額を入力してね(1~999,999)'))
                udb[id]['status'] = 'modify_amount'
            if event.message.text == u'支払項目':
                reply_msgs.append(TextSendMessage(text = u'何の金額か教えて(ex.レンタカー代)'))
                udb[id]['status'] = 'modify_use'
            if event.message.text == u'写真':
                reply_msgs.append(TextSendMessage(text = u'写真を撮るか、写真を選択してね'))
                udb[id]['status'] = 'modify_photo'

        elif status == 'modify_amount':
            if event.message.text.isdigit():
                amount = int(event.message.text)
                if (amount < 1) | (amount > 999999):
                    reply_msgs.append(TextSendMessage(text = u'入力できるのは1〜999,999円だよ'))

                else:
                    # udb[id]['status'] = 'input_use'
                    udb[id]['amount'] = amount
                    reply_msgs.append(TemplateSendMessage(
                        alt_text='登録確認',
                        template=ButtonsTemplate(
                            thumbnail_image_url=udb[id].get('image_url', None),
                            # title=u'登録確認',
                            text = u'{use}で{amount}円、これで登録してよいですか？'.format(use = udb[id]['use'], amount = get_commad_number_str(udb[id]['amount'])),
                            actions=[
                                MessageTemplateAction(
                                # PostbackTemplateAction(
                                    label=u'OK',
                                    text=u'OK',
                                    # data='action=buy&itemid=1'
                                ),
                                MessageTemplateAction(
                                # PostbackTemplateAction(
                                    label=u'訂正する',
                                    text=u'訂正する',
                                    # data='action=buy&itemid=1'
                                ),
                            ]
                        )
                    ))
                    udb[id]['status'] = 'confirm_modify'

            else:
                reply_msgs.append(TextSendMessage(text = u'入力できるのは1〜999,999円だよ'))


        elif status == 'modify_use':
            udb[id]['use'] = event.message.text
            reply_msgs.append(TemplateSendMessage(
                alt_text='登録確認',
                template=ButtonsTemplate(
                    thumbnail_image_url=udb[id].get('image_url', None),
                    # title=u'登録確認',
                    text = u'{use}で{amount}円、これで登録してよいですか？'.format(use = udb[id]['use'], amount = get_commad_number_str(udb[id]['amount'])),
                    actions=[
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'OK',
                            text=u'OK',
                            # data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                        # PostbackTemplateAction(
                            label=u'訂正する',
                            text=u'訂正する',
                            # data='action=buy&itemid=1'
                        ),
                    ]
                )
            ))
            udb[id]['status'] = 'confirm_modify'

        elif status == 'confirm_modify':
            if event.message.text == u'OK':
                reply_msgs.append(TextSendMessage(text = u'登録完了しました！この内容でみんなに報告しますね！'))
                # ここでDB登録＆みんなに報告
                groups = db.get_user_groups(id)
                for gid in groups:
                    db.add_payment(gid, id, udb[id]["amount"], udb[id].get("use"), udb[id].get("image_url"))

                    msgs = []
                    name = get_name(id)
                    if "use" in udb[id]:
                        msgs.append(TextSendMessage(text = u'{}さんが{}に{}円支払いました'.format(name, udb[id].get("use"), udb[id]["amount"])))
                    else:
                        msgs.append(TextSendMessage(text = u'{}さんが{}円支払いました'.format(name, udb[id]["amount"])))
                    if "image_url" in udb[id]:
                        msgs.append(ImageSendMessage(original_content_url = udb[id]["image_url"], preview_image_url = udb[id]["image_url"]))
                    line_bot_api.push_message(gid, msgs)

                del udb[id]
            elif event.message.text == u'訂正する':
                reply_msgs.append(TemplateSendMessage(
                    alt_text=u'支払訂正ボタン',
                    template=ButtonsTemplate(
                        # thumbnail_image_url='https://example.com/image.jpg',
                        title=u'支払訂正',
                        text=u'訂正する項目をリストから選んでね',
                        actions=[
                            # PostbackTemplateAction(
                            MessageTemplateAction(
                                label=u'金額',
                                text=u'金額',
                                # data='action=buy&itemid=1'
                            ),
                            MessageTemplateAction(
                                label=u'支払項目',
                                text=u'支払項目',
                                # data='action=buy&itemid=1'
                            ),
                            # PostbackTemplateAction(
                            MessageTemplateAction(
                                label=u'写真',
                                text=u'写真',
                                # data='action=buy&itemid=1'
                            ),
                        ]
                    )
                ))
                udb[id]['status'] = 'modify_payment'

            else:
                reply_msgs.append(TextSendMessage(text = u'ボタンで選んでね'))

        elif status in ['add_photo', 'modify_photo']:
            reply_msgs.append(TextSendMessage(text = u'写真を撮るか、写真を選択してね'))

        elif status == 'set_rate':
            if event.message.text.isdigit():
                rate = int(event.message.text)
                if (rate < 1) | (rate > 99):
                    reply_msgs.append(TextSendMessage(text = u'入力できるのは1〜99だよ'))

                else:
                    reply_msgs.append(TextSendMessage(text = u'『対象ユーザ』さんの傾斜割合を{rate}に設定しました'.format(rate=get_commad_number_str(rate))))

            else:
                reply_msgs.append(TextSendMessage(text = u'入力できるのは1〜99だよ'))

        if(event.message.text == u'バイバイ'):
            # del_warikan_group(event.source)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=u'またね'))
            if(event.source.type == 'group'):
                line_bot_api.leave_group(event.source.group_id)
                gid = event.source.group_id
            elif(event.source.type == 'room'):
                line_bot_api.leave_room(event.source.room_id)
                gid = event.source.room_id
            db.delete_group(gid)

        if(event.message.text == u'リンク'):
            if(event.source.type == 'group'):
                gid = event.source.group_id
            elif(event.source.type == 'room'):
                gid = event.source.room_id
            reply_msgs.append(TextSendMessage(text = line_friend_url))
            reply_msgs.append(ImageSendMessage(original_content_url = line_qr_url, preview_image_url = line_qr_url))

            link_uri='https://access.line.me/dialog/oauth/weblogin?response_type=code&client_id={}&redirect_uri={}&state={}'.format(line_login_channel_id, urllib.quote(auth_url), gid)
            reply_msgs.append(ImagemapSendMessage(
                base_url=base_url + '/images/LINELogin',
                alt_text='this is an imagemap',
                base_size=BaseSize(height=302, width=1040),
                actions=[
                    URIImagemapAction(
                        link_uri=link_uri,
                        area=ImagemapArea(x=0, y=0, width=1040, height=302)
                    ),
                ]
            ))

    # if len(reply_msgs) == 0:
    #     reply_msgs.append(TextSendMessage(text = udb[id]['status']))

    if len(reply_msgs):
        try:
            line_bot_api.reply_message(event.reply_token, reply_msgs)
        except LineBotApiError as e:
            print_error(e)

def save_content(message_id, filename):
    message_content = line_bot_api.get_message_content(message_id)
    with open(filename, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    id = get_id(event.source)
    reply_msgs = []

    try:
        status = udb[id]['status']
    except:
        status = 'none'
    print status

    if status in ['add_photo', 'modify_photo']:
        udb[id]['image_url'] = base_url + '/static/' + event.message.id + '.jpg'
        save_content(event.message.id, 'static/' + event.message.id + '.jpg')

        reply_msgs.append(TemplateSendMessage(
            alt_text='登録確認',
            template=ButtonsTemplate(
                thumbnail_image_url=udb[id].get('image_url', None),
                # title=u'登録確認',
                text = u'{use}で{amount}円、これで登録してよいですか？'.format(use = udb[id]['use'], amount = get_commad_number_str(udb[id]['amount'])),
                actions=[
                    MessageTemplateAction(
                    # PostbackTemplateAction(
                        label=u'OK',
                        text=u'OK',
                        # data='action=buy&itemid=1'
                    ),
                    MessageTemplateAction(
                    # PostbackTemplateAction(
                        label=u'訂正する',
                        text=u'訂正する',
                        # data='action=buy&itemid=1'
                    ),
                ]
            )
        ))
        udb[id]['status'] = 'confirm_modify'

    if len(reply_msgs) == 0:
        reply_msgs.append(TextSendMessage(text = udb[id]['status']))

    line_bot_api.reply_message(event.reply_token, reply_msgs)

@handler.add(MessageEvent, message=VideoMessage)
def handle_video_message(event):
    pass

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    pass

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    pass

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    pass

@handler.add(FollowEvent)
def handle_follow_message(event):
    pass

@handler.add(UnfollowEvent)
def handle_unfollow_message(event):
    pass


@handler.add(JoinEvent)
def handle_join_message(event):
    # add_friendsdb(event.source)

    if event.source.type == 'group':
        gid = event.source.group_id
    elif event.source.type == 'room':
        gid = event.source.room_id

    msgs=[]

    text = u'はじめまして、Checkunです。このグループの会計係をさせていただきます！\n' \
        u'まずは、このグループメンバー全員の方とお友達になりたいです。\n' \
        u'次のURLかQRコードで友達になってね。\n' \
        u'友達になったら下のログインボタンで清算グループに入ってね。' \
        # u'グループのスタンプを決めて送ってね'
        # u'左のボタンを押して私と友達になって、右のボタンで清算グループに入ってください！'
    msgs.append(TextSendMessage(text = text))

    msgs.append(TextSendMessage(text = line_friend_url))
    msgs.append(ImageSendMessage(original_content_url = line_qr_url, preview_image_url = line_qr_url))

    link_uri='https://access.line.me/dialog/oauth/weblogin?response_type=code&client_id={}&redirect_uri={}&state={}'.format(line_login_channel_id, urllib.quote(auth_url), gid)
    msgs.append(ImagemapSendMessage(
        base_url=base_url + '/images/LINELogin',
        alt_text='this is an imagemap',
        base_size=BaseSize(height=302, width=1040),
        actions=[
            URIImagemapAction(
                link_uri=link_uri,
                area=ImagemapArea(x=0, y=0, width=1040, height=302)
            ),
        ]
    ))

    line_bot_api.reply_message(event.reply_token, msgs)

    db.add_group(gid,event.source.type)
    # add_warikan_group(event.source)

@handler.add(LeaveEvent)
def handle_leave_message(event):
    if event.source.type == 'group':
        gid = event.source.group_id
    elif event.source.type == 'room':
        gid = event.source.room_id
    db.delete_group(gid)


@handler.add(PostbackEvent)
def handle_postback_event(event):
    pass


@handler.add(BeaconEvent)
def handle_beacon_event(event):
    pass


if __name__ == "__main__":
    app.run(debug=True, port=5000)
    # app.run(debug=True, port=5001)
