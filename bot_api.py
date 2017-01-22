#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

line_group_id = os.environ['LINE_GROUP_ID']
line_group_name = os.environ['LINE_GROUP_NAME']
line_group_total_amount = 0
line_group_average_amount = 0
line_group_user_count = os.environ['LINE_GROUP_USER_COUNT']

if (line_group_user_count == None):
	line_group_user_count = 0

line_group_users = []

if (line_group_user_count > 0):
	for i in range(1, lint_group_user_count+1):
		#(id, amount)
		line_group_users.append((os.environ['LINE_GROUP_USER_' + str(i)], 0))

#グループ保存
def save_group(group_id, group_name):
	line_group_id = group_id
	line_group_name = group_name

	os.environ['LINE_GROUP_ID'] = line_group_id
	os.environ['LINE_GROUP_NAME'] = line_group_name

#精算人数確定用
#幹事さんがメンバーをグループに追加した場合
#WebhookのJoin Event(group_id)が通知されるので、各グループのメンバー数をカウント（イングリメント）
#デモではとりあえず1グループ
def user_count(group_id):
	line_group_user_count+=1

	os.environ['LINE_GROUP_USER_COUNT'] = line_group_user_count

#各メンバーががbotを追加した場合(Eventある？)
#或いは、bot追加後最初のメッセージを送った場合、ユーザー情報を保存
#幹事さんに追加されたグループと紐付けするために、グループ名(或いはあい言葉?)のmessageを送る必要があるので、
#指定グループにユーザーを保存
#内部で管理するグループのテーブルから、グループ名をgroup_idに変換が必要
#デモではとりあえず1グループ
def save_user(group_id, user_id):
	if (user_id not in line_group_users):
		line_group_users.append((user_id, 0)
		os.environ['LINE_GROUP_USER_' + str(i)] = user_id

#同じメンバーが複数のグループに入っている可能性があるので、
#xxxのmessageを送った場合、精算するグループ一覧を返す。
#デモでは1グループなので、とりあえず対応不要
def get_groups(user_id):
	return line_group_name

#メンバーが送った金額を保存する。
#どのグループの精算金額なのか、ユーザーごとに対象グループの状態を保持する必要がある(1グループなので、とりあえず不要)
#複数回送る可能性があるので、金額をリストで保持(デモではとりあえず、１回のみ)
#買い出しなど支払いが発生していないメンバーはmessageの送信が不要なので、金額は0
def set_amount(group_id, user_id, amount):
	line_group_users[user_id][1] = amount

#指定グループの合計額を計算
#グループ内の各メンバーの設定金額を足す
def calculate_total_amount(group_id):
	for index, user in enumerate(line_group_users):
		line_group_total_amount += user[1]

	#return line_group_total_amount

#平均金額を計算(合計額/メンンバー数)
def calculate_average_amount(group_id):
	user_len = len(line_group_users)

	if (len > 0):
		line_group_average_amount = line_group_total_amount / len

#指定グループのメンバーの精算額を計算して返す
#精算ボターンを押した場合（幹事さんが?）
#平均金額-設定金額
#+金額の場合、幹事さんに支払う
#-金額の場合、幹事さんから払い戻す
def adjust_amount(group_id, user_id):
	user_amount = line_group_users[user_id][1]

	return line_group_average_amount - user_amount

#ユーザーが送信した/TemplateMessageで送信したmessageを解析
#一例
#help(使い方)：help/?/...などのmessageを送った時
#group(所属グループ一覧):groupのmessageを送った時
#金額:¥数値のmessageを送った時
#Yes/No:xxx/Confirmボターンを押した時
#その他
def analyze_message(message):
    pass


#ここからはSend Message Object作成用

#helpメッセージ
#固定の文字列かTemplateMessage?
def create_help():
    pass

#２つのアクションボタンを提示するTemplateMessage
def create_confirm():
    pass

#
def create_imagemap():
    pass

#AITalkを使って、textから音声ファイルを作成
def create_audio(text):
    pass


#幹事さんがグループを作成後、メンバーを追加し、botへ招待(botがbotのurlをグループへ発信)
#各メンバーはbotのurlをクリックして、botを追加
def create_url_bot():
    pass


#要る?
def create_url_group(group_id):
    pass
