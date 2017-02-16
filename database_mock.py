#!/usr/bin/python
# -*- coding: utf-8 -*-

#user table
#groups table
#payments table
#debt table?

def add_user(uid,name,pict,status,follow):
    ''' ユーザ追加 '''

def get_user(uid):

#必要なら分割update_user_xxx
def update_user(uid,name,pict,status,follow):



def add_group(gid,type,name=None):
    ''' グループ追加
        name(Noneの場合), users, accountant, settlement_users, round は生成'''

#必要なら分割update_group_xxx
def update_group(gid, name=None, accountant=None, round=None):


def delete_group(gid):
    ''' グループ削除 '''

def add_user_to_group(uid, gid):

def delete_user_from_group(uid, gid):

def get_user_groups(uid):
    ''' table(group)のusersにuidが含まれるグループデータをリストで渡す '''
    groups = []
    return groups

#とりあえずsettlement_usersを使用。usersにflag追加しても対応可能
def add_settlement_user_to_group(gid, uid):

def delete_settlement_user_from_group(gid, uid):

#usersではなくsettlement_usersから?userが所属するすべてのgroupの支払い一覧を返す?
def get_user_groups_payments(uid):
    ''' table(group)のusersにuidが含まれるグループのpaymentsをリストで渡す '''
    peyments = []
    return payments

#paymentsで管理?
def set_group_debt_uid_list(gid, uid_list):
    ''' table(group) の debt_uid を uid_list にする '''




def add_payment(gid, payment_uid, amount=None, description=None, image=None):
    ''' table(payments) に新しい支払を追加
        id, payment_date, modification_date は生成する
        imageの指定があれば、s3にアップ'''

def delete_payment(payment_id):
    ''' table(payments) の id=payment_id を削除 or 不可視にする '''

def update_payment(payment_id, amount=None, description=None, image=None):
    ''' table(payments) の amount, description, image を上書きする
        modification_date更新 
        imageの指定があれば、s3にアップ'''

#金額〜最終更新日時情報
def get_user_payment_info(gid, uid):

#全groupでの支払いりすと
def get_user_payment_amounts(uid):
    ''' table(payments) からuserのamountりすとを渡す '''

#指定groupで支払いりすと
def get_user_group_payment_amounts(gid, uid):
    ''' table(group)のusersにuidが含まれるグループのpaymentsをリストで渡す '''

#debt
#独立tableでも、groupに追加しても良い
#誰が誰に支払いするかの一覧になる


if __name__ == "__main__":
    pass
