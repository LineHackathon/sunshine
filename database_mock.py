#!/usr/bin/python
# -*- coding: utf-8 -*-

def add_user(uid,name,pict,status,follow):
    ''' ユーザ追加 '''

def add_group(gid,type):
    ''' グループ追加
        name, users, accountant, settlement_users, round は生成'''

def delete_group(gid):
    ''' グループ削除 '''

def get_user_groups(uid):
    ''' table(group)のusersにuidが含まれるグループデータをリストで渡す '''
    groups = []
    return groups

def get_user_groups_payments(uid):
    ''' table(group)のusersにuidが含まれるグループのpaymentsをリストで渡す '''
    peyments = []
    return payments

def set_debt_uid_list(gid, uid_list):
    ''' table(group) の debt_uid を uid_list にする '''

def add_payment(gid, payment_uid, amount=None, description=None, image=None):
    ''' table(payments) に新しい支払を追加
        id, payment_date, modification_date は生成する'''

def delete_payment(payment_id):
    ''' table(payments) の id=payment_id を削除 or 不可視にする '''

def update_payment(paymentid, amount=None, description=None, image=None):
    ''' table(payments) の amount, description, image を上書きする '''

def create_group(gid):
    ''' table(payments) の amount, description, image を上書きする '''


if __name__ == "__main__":
    pass
