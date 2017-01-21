#!/usr/bin/python
# -*- coding: utf-8 -*-


#精算人数確定用
#幹事さんがメンバーをグループに追加した場合
#WebhookのJoin Event(group_id)が通知されるので、各グループのメンバー数をカウント（イングリメント）
#デモではとりあえず1グループ
def user_count(group_id):
	

#各メンバーががbotを追加した場合(Eventある？)
#或いは、bot追加後最初のメッセージを送った場合、ユーザー情報を保存
#幹事さんに追加されたグループと紐付けするために、グループ名(或いはあい言葉?)のmessageを送る必要があるので、
#指定グループにユーザーを保存
#内部で管理するグループのテーブルから、グループ名をgroup_idに変換が必要
#デモではとりあえず1グループ
def save_user(group_id, user_id):


#同じメンバーが複数のグループに入っている可能性があるので、
#xxxのmessageを送った場合、精算するグループ一覧を返す。
#デモでは1グループなので、とりあえず対応不要
def get_groups(user_id):


#メンバーが送った金額を保存する。
#どのグループの精算金額なのか、ユーザーごとに対象グループの状態を保持する必要がある(1グループなので、とりあえず不要)
#複数回送る可能性があるので、金額をリストで保持(デモではとりあえず、１回のみ)
#買い出しなど支払いが発生していないメンバーはmessageの送信が不要なので、金額は0
def set_amount(group_id, user_id, amount):


#指定グループの合計額を計算
#グループ内の各メンバーの設定金額を足す
def calculate_total_amount(group_id):


#平均金額を計算(合計額/メンンバー数)
def calculate_average_amount(group_id):

#指定グループのメンバーの精算額を計算して返す
#精算ボターンを押した場合（幹事さんが?）
#平均金額-設定金額
#+金額の場合、幹事さんに支払う
#-金額の場合、幹事さんから払い戻す
def adjust_amount(group_id, user_id):


#ユーザーが送信した/TemplateMessageで送信したmessageを解析
#一例
#help(使い方)：help/?/...などのmessageを送った時
#group(所属グループ一覧):groupのmessageを送った時
#金額:¥数値のmessageを送った時
#Yes/No:xxx/Confirmボターンを押した時
#その他
def analyze_message(message):


#ここからはSend Message Object作成用

#helpメッセージ
#固定の文字列かTemplateMessage?
def create_help():

#２つのアクションボタンを提示するTemplateMessage
def create_confirm():

#
def create_imagemap():

#AITalkを使って、textから音声ファイルを作成
def create_audio(text):


#幹事さんがグループを作成後、メンバーを追加し、botへ招待(botがbotのurlをグループへ発信)
#各メンバーはbotのurlをクリックして、botを追加
def create_url_bot():


#要る?
def create_url_group(group_id):

