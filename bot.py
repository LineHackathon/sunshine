#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
base_url = os.environ['LINE_BASE_URL']

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


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    print(event)
    if(event.source.type == 'user'):
        print_profile(event.source.user_id)
        print(u'user')
        print(event.source.user_id)
        print(event.message.text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))
        pass

    if(event.source.type == 'group'):
        print(u'group')
        print(event.source.group_id)
        print(event.message.text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))
        pass

def save_content(message_id, filename):
    message_content = line_bot_api.get_message_content(message_id)
    with open(filename, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    print(event)
    save_content(event.message.id, 'static/' + event.message.id + '.jpg')
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=u'画像ありがと'))

@handler.add(MessageEvent, message=VideoMessage)
def handle_video_message(event):
    print(event)
    save_content(event.message.id, 'static/' + event.message.id + '.mp4')
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=u'動画ありがと'))

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    print(event)
    save_content(event.message.id, 'static/' + event.message.id + '.m4a')
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=u'音声ありがと'))

@handler.add(PostbackEvent)
def handle_postback_message(event):
    print(event)
    print(event.postback.data)


if __name__ == "__main__":
    app.run(debug=True)
