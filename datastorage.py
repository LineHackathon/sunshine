#!/usr/bin/python
# -*- coding: utf-8 -*-

from tinydb import TinyDB, Query

#user table
#groups table
#payments table
#debt table?

print('get db start')
#test_db = TinyDB('db/test.json')
#test_db_file = aws3.get_db('test1')
#print(test_db_file)
#test_db = TinyDB(test_db_file)

#db_file = aws3.get_db('checkun')
#test
db_file = 'db/checkun.json'
print(db_file)
db = TinyDB(db_file, indent=2, sort_keys=True, separators=(',', ': '))
print('get db end')

user_table = db.table('users')
group_table = db.table('groups')
payment_table = db.table('payments')
debt_table = db.table('debt')

def update_db():
    #aws3.update_db(checkun)
    pass


###################
# user table
###################
def add_user(uid, name, pict, status, follow):
    ''' ユーザ追加 '''
    if is_user_exist(uid):
        update_user(uid,name,pict,status,follow)
    else:
        user_table.insert({'uid':uid, 'name':name, 'pict':pict, 'status':status, 'follow':follow})

    #save pict to user folder in S3
    if pict is not None:
        #aws3.set_user_pict(uid, pict)
        pass

    update_db()

#return list
def get_user(uid):
    return user_table.search(Query().uid == uid)

#必要なら分割update_user_xxx
def update_user(uid,name,pict,status,follow):
    user_table.update({'uid':uid, 'name':name, 'pict':pict, 'status':status, 'follow':follow}, Query().uid == uid)
    update_db()

#return list
def get_users():
    return user_table.all()
    #return user_table.get(Query().uid == 'uid')
    #return user_table.get(eid = 'uid')

def delete_user(uid):
    user_table.remove(Query().uid == uid)
    update_db()

def delete_all_users():
    user_table.purge()
    update_db()

def is_user_exist(uid):
    return user_table.contains(Query().uid == uid)

###################
# group table
###################
def add_group(gid,gtype,name=None):
    ''' グループ追加
        name(Noneの場合), users, accountant, settlement_users, round は生成'''

    if is_group_exist(gid):
        update_group(gid, name)
    else:
        if name is None:
            #todo:
            name = gid

        users = []
        accountant = False
        settlement_users = []
        round_value = 100

        group_table.insert({
                            'gid':gid,
                            'type':gtype,
                            'name':name,
                            'users':users,
                            'accountant':accountant,
                            'settlement_users':settlement_users,
                            'round_value':round_value})

    update_db()

#必要なら分割update_group_xxx
def update_group(gid, name=None, accountant=None, round_value=None):
    group = {}
    if name is not None:
        group['name'] = name

    if accountant is not None:
        group['accountant'] = accountant

    if round_value is not None:
        group['round_value'] = round_value

    group_table.update(group, Query().gid == gid)

    update_db()

def get_groups():
    return group_table.all()
    #return group_table.get(eid = 'gid')

def get_group_info(gid):
    group_info = {}

    group = group_table.search(Query().gid == gid)

    if group:
        print(group[0])
        return group[0]
    return None

def delete_group(gid):
    ''' グループ削除 '''
    group_table.remove(Query().gid == gid)
    # payment_table.remove(Query().gid == gid)

    update_db()

def delete_all_groups():
    group_table.purge()
    update_db()


def add_user_to_group(uid, gid):
    group = group_table.search(Query().gid == gid)

    #if group is not None:
    if len(group) == 1:
        users = group[0]['users']
        for user_id in users:
            if user_id == uid:
                return

        users.append(uid)
        group[0]['users'] = users
        group_table.update(group[0], Query().gid == gid)

        update_db()

def get_group_users(gid):
    users = []

    group = group_table.search(Query().gid == gid)

    #if group is not None:
    if len(group) == 1:
        users = group[0]['users']

    return users

def delete_user_from_group(gid, uid):
    group = group_table.search(Query().gid == gid)

    #if group is not None:
    if len(group) == 1:
        users = group[0]['users']
        for user_id in users:
            if user_id == uid:
                users.remove(user_id)
                break

        group[0]['users'] = users
        group_table.update(group[0], Query().gid == gid)

        update_db()

def get_user_groups(uid):
    ''' table(group)のusersにuidが含まれるグループデータをリストで渡す '''
    groups = []

    all_groups = group_table.all()
    for g in all_groups:
        users = g['users']
        for user_id in users:
            if user_id == uid:
                groups.append(g['gid'])
                break

    return groups

#とりあえずsettlement_usersを使用。usersにflag追加しても対応可能
def add_settlement_user_to_group(gid, uid):
    group = group_table.search(Query().gid == gid)

    #if group is not None:
    if len(group) == 1:
        users = group[0]['settlement_users']
        for user_id in users:
            if user_id == uid:
                return

        users.append(uid)
        group[0]['settlement_users'] = users
        group_table.update(group[0], Query().gid == gid)

        update_db()

def get_group_settlement_users(gid):
    settlement_users = []

    group = group_table.search(Query().gid == gid)

    #if group is not None:
    if len(group) == 1:
        settlement_users = group[0]['settlement_users']

    return settlement_users

def delete_settlement_user_from_group(gid, uid):
    group = group_table.search(Query().gid == gid)

    #if group is not None:
    if len(group) == 1:
        users = group[0]['settlement_users']
        for user_id in users:
            if user_id == uid:
                users.remove(user_id)
                break

        group[0]['settlement_users'] = users
        group_table.update(group[0], Query().gid == gid)

        update_db()

def get_groups_payments(gid):
    return payment_table.search(Query().gid == gid)

#usersではなくsettlement_usersから?userが所属するすべてのgroupの支払い一覧を返す?
def get_user_groups_payments(uid):
    ''' table(group)のusersにuidが含まれるグループのpaymentsをリストで渡す '''
    payments = payment_table.search(Query().gid == gid)
    return payments

#paymentsで管理?
def set_group_debt_uid_list(gid, uid_list):
    ''' table(group) の debt_uid を uid_list にする '''

def is_group_exist(gid):
    return group_table.contains(Query().gid == gid)

def is_group_user_exist(gid, uid):
    group = group_table.search(Query().gid == gid)

    #if group is not None:
    if len(group) == 1:
        users = group[0]['settlement_users']
        for user_id in users:
            if user_id == uid:
                return True

    return False


###################
# payment table
###################
def add_payment(gid, payment_uid, amount=None, description=None, receipt=None):
    ''' table(payments) に新しい支払を追加
        id, payment_date, modification_date は生成する
        imageの指定があれば、s3にアップ'''

    p_id = len(payment_table) + 1
    #todo
    payment_date = '2017/02/28'
    modification_date = payment_date
    payment_table.insert({  'gid':gid,
                            'payment_uid':payment_uid,
                            'p_id':p_id,
                            'amount':amount,
                            'description':description,
                            'receipt':receipt,
                            'payment_date':payment_date,
                            'modification_date':modification_date
                        })

    #save receipt to user folder in S3
    if receipt is not None:
        #aws3.set_receipt(uid, receipt)
        pass

    update_db()

def get_payments():
    return payment_table.all()

def delete_payment(payment_id):
    ''' table(payments) の id=payment_id を削除 or 不可視にする '''
    payment_table.remove(Query().payment_id == payment_id)

    update_db()

def update_payment(payment_id, amount=None, description=None, receipt=None):
    ''' table(payments) の amount, description, image を上書きする
        modification_date更新
        imageの指定があれば、s3にアップ'''
    payment = {}

    if amount is not None:
        payment['amount'] = amount

    if description is not None:
        payment['description'] = description

    if receipt is not None:
        payment['receipt'] = receipt
        #save receipt to user folder in S3
        #aws3.set_receipt(uid, receipt)

    #todo
    modification_date = '2017/02/28'
    payment['modification_date'] = modification_date
    payment_table.insert(payment, Query().payment_id == payment_id)

    update_db()

#指定groupの全ユーザーのpaymentリスト
def get_group_payment_payments(gid):
    ''' table(payments) からuserのamountりすとを渡す '''
    return payment_table.search(Query().gid == gid)

#指定group、指定ユーザーのpaymentリスト
def get_group_user_payments(gid, payment_uid):
    return payment_table.search(Query().pid == gid and Query().payment_uid == payment_uid)


#debt
#独立tableでも、groupに追加しても良い
#誰が誰に支払いするかの一覧になる


if __name__ == "__main__":
    pass
