#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

import warikan

# import sqlite3
uname_dict = {}
uid_dict = {}

app = Flask(__name__)

f = open('sunshine_bot.json', 'r')
json_dict = json.load(f)
line_bot_api = LineBotApi(json_dict['token'])
handler = WebhookHandler(json_dict['secret'])
base_url = json_dict['base_url']
f.close

print(base_url)

@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

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

def print_profile(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        print(profile.display_name)
        print(profile.user_id)
        print(profile.picture_url)
        print(profile.status_message)
    except linebot.LineBotApiError as e:
        print_error(e)

def get_name(uid):
    # print_profile(event.source.uid)
    if(uid in uname_dict):
        name = uname_dict[uid]
    else:
        name = line_bot_api.get_profile(uid).display_name
        uname_dict[uid] = name
        uid_dict[name] = uid
    return name


@handler.add(FollowEvent)
def handle_follow_message(event):
    msg = u'はじめまして、Checkunです。友達登録していただきありがとうございます。清算のやり取りをおこなうグループに私を招待してください。そこで発行されるグループIDを入力してください'
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg))


@handler.add(JoinEvent)
def handle_join_message(event):
    # print(event)
    # msg = u'空前絶後のぉ〜〜〜〜〜〜'
    if(event.source.type == 'group'):
        # group_id_temp = event.source.group_id
        msg = \
            u'はじめまして、Checkunです。このグループの会計係をさせていただきます！\n' \
            u'ますは、このグループメンバー全員の方とお友達になりたいです。\n' \
            u'次のURLから私と友達になって、以下のグループIDをコピー＆ペーストしてください！\n' \
            u'https://line.me/R/ti/p/lvTHsDPv_o\n'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(msg))

        line_bot_api.push_message(event.source.group_id,
            TextSendMessage(str(event.source.group_id)))
        # line_bot_api.push_message(
        #     event.source.group_id,
        #     TextSendMessage(text=u'グループIDは' + event.source.group_id + u'です'))

        # グループIDの割り勘DBを作成
        warikan.set_groupid(event.source.group_id)

def get_template_msg():
    confirm_template_message = TemplateSendMessage(
        alt_text='Confirm Checkout',
        template=ConfirmTemplate(
            text=u'精算を開始しますか？',
            actions=[
                PostbackTemplateAction(
                    label='OK',
                    text='精算をお願いします',
                    data='start checkout'
                ),
                PostbackTemplateAction(
                    label='cancel',
                    text='精算を中止してください',
                    data='cancel checkout'
                ),
            ]
        )
    )
    return confirm_template_message

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    # print(event)
    if(event.source.type == 'user'):
        uid = event.source.user_id
        name = get_name(uid)

        print(warikan.group_id)
        print(event.message.text)

        if(event.message.text == warikan.group_id):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='グループとつながりました！'))
            warikan.add_user(uid)
            msg = name + u'さんがグループIDとつながりました！'
            line_bot_api.push_message(
                warikan.group_id,
                TextSendMessage(text=msg))


        elif(event.message.text.isdigit()):
            amount = int(event.message.text)
            msg = name + u'さんが' + str(amount) + u'円支払いました'
            line_bot_api.push_message(
                warikan.group_id,
                TextSendMessage(text=msg))
            warikan.add_amount(uid, amount)

            msg = name + u'さんは合計' + str(warikan.amount_dict[uid]) + u'円支払いました'
            # msg = name + u'さんは合計{:,d}円支払いました'.format(warikan.amount_dict[uid])
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=msg))
            pass

        elif(event.message.text == u'支払入力をはじめる'):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=u'みなさんのために何か支払われたのですね。支払われた金額を入力してください'))
            pass

        elif(event.message.text == u'支払内容を確認する'):
            msg = u'現時点の支払内容をご報告します\n'
            total = 0
            for uid in warikan.amount_dict:
            # for uid in amount_dict:
                msg += get_name(uid) + u'さんが' + str(warikan.amount_dict[uid]) + u'円支払いました\n'
            # ave = total / len(amount_dict)
            ave = warikan.get_average()
            msg += u'一人あたり' + str(ave) + u'円です'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=msg))
            # line_bot_api.reply_message(
            #     event.reply_token,
            #     TextSendMessage(text=(
            #         u'Aさんが15400円使用しました\n'
            #         u'Bさんが2000円使用しました\n'
            #         u'Cさんが1200円使用しました\n'
            #         u'Dさんが0円使用しました\n'
            #         u'一人あたり4650円です'
            #         )))
            pass

        elif(event.message.text == u'精算をお願いします'):
            msg = u'一人あたり' + str(warikan.get_average()) + u'円です'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=msg))

            line_bot_api.push_message(warikan.group_id, get_template_msg())
            pass
        elif(event.message.text == u'ヘルプ'):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=u'申し訳ございません\n準備中です'))
            pass
        else:
            print(u'user')
            print(event.source.user_id)
            print(event.message.text)
            # line_bot_api.reply_message(
            #     event.reply_token,
            #     TextSendMessage(text=event.message.text))
            line_bot_api.push_message(
                warikan.group_id,
                TextSendMessage(text=event.message.text))
        pass

    if(event.source.type == 'group'):
        print(u'group')
        print(event.source.group_id)
        print(event.message.text)
        # group_id_temp = event.source.group_id
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=event.message.text))
        pass

def save_content(message_id, filename):
    message_content = line_bot_api.get_message_content(message_id)
    with open(filename, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # print(event)
    if(event.source.type == 'user'):
        save_content(event.message.id, 'static/' + event.message.id + '.jpg')
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=u'ありがとう\n画像をみんなにシェアするね'))
        # print('groupid:' + group_id_temp)
        line_bot_api.push_message(
            warikan.group_id,
            TextSendMessage(text=get_name(event.source.user_id) + u'が画像をシェアしてくれたよ'))
        line_bot_api.push_message(
            warikan.group_id,
            ImageSendMessage(
                original_content_url=base_url + '/static/' + event.message.id + '.jpg',
                preview_image_url=base_url + '/static/' + event.message.id + '.jpg'
            )
        )

def make_paypal_img_msg(url):
    imagemap_message = ImagemapSendMessage(
        base_url='https://www.paypal.jp/jp/mms2/service/logos-buttons/images/CO_228_44.png',
        alt_text='PayPal',
        base_size=BaseSize(height=200, width=1040),
        actions=[
            URIImagemapAction(
                link_uri=url,
                area=ImagemapArea(
                    x=0, y=0, width=200, height=1040
                )
            ),
        ]
    )
    return imagemap_message

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
                msg = u'に{:,d}円払ってください\n'.format(-payment_dict[uid][pay])
            else:
                msg = u'から{:,d}円受け取ってください\n'.format(payment_dict[uid][pay])
            grpmsg += msg
            pmsg += msg

        line_bot_api.push_message(
            uid,
            TextSendMessage(text=pmsg))
        # print(pmsg)


    if(grpmsg == ''):
        grpmsg = '精算はありません'
    line_bot_api.push_message(
        warikan.group_id,
        TextSendMessage(text=grpmsg))
    # print(grpmsg)

    # paypalリンク作成
    # http://944ce050.ngrok.io/vault_sale?amount=xxx
    # https://www.paypal.jp/jp/mms2/service/logos-buttons/images/CO_228_44.png
    for uid in payment_dict:
        for pay in payment_dict[uid]:
            if(payment_dict[uid][pay] < 0):
                url = 'http://944ce050.ngrok.io/vault_sale?amount=' + str(-payment_dict[uid][pay])
                print(url)
                # line_bot_api.push_message(
                #     uid,
                #     make_paypal_img_msg(url))
                line_bot_api.push_message(
                    uid,
                    TextSendMessage(url))



@handler.add(PostbackEvent)
def handle_postback_message(event):
    # print(event)
    print(event.postback.data)
    if(event.postback.data == u'start checkout'):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=u'精算を始めます'))

        start_warikan()

    elif(event.postback.data == u'cancel checkout'):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=u'おっと、焦りは禁物ですよ\n精算を中止します'))
        pass

if __name__ == "__main__":
    warikan.load_json(warikan.db_fname)
    app.run(debug=True)
