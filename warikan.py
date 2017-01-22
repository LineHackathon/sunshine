#!/usr/bin/python
# -*- coding: utf-8 -*-

# import yaml
import json
import pprint

group_id = ''
amount_dict = {}
payment_dict = {}

db_fname = 'warikan.json'
# load_json(db_fname)

def set_groupid(gid):
    global group_id
    group_id = gid
    save_json(db_fname)

def add_user(uid):
    global amount_dict
    amount_dict[uid] = 0
    save_json(db_fname)

def add_amount(uid, amount):
    global amount_dict
    amount_dict[uid] += amount
    save_json(db_fname)

def get_amount(user):
    return amount_dict[user]

def get_total():
    return sum(amount_dict.values())

def get_average():
    if(len(amount_dict) == 0):
        return 0
    return get_total() / len(amount_dict)

def get_payment(user):
    return payment_dict[user]

def load_json(fname):
    f = open(fname, 'r')
    json_dict = json.load(f)
    # print(json_dict)
    global group_id
    global amount_dict
    group_id = json_dict['group_id']
    amount_dict = json_dict['amount']
    f.close

def save_json(fname):
    f = open(fname, 'w')
    f.write(json.dumps({
        'group_id': group_id,
        'amount': amount_dict,
    }, ensure_ascii=False, indent=2, sort_keys=True, separators=(',', ': ')))
    f.close

def calc_warikan():
    # 4. 割り勘金額の計算
    #  4-1. Botサーバー内で保持されている『ユーザー数』と『合計金額』を使用して以下の計算を行う。
    #       『合計金額』÷『ユーザー数』
    #  4-2.計算結果を少数以下を繰り上げて『割り勘金額』の変数に保持する
    warikan_kingaku = get_average()
    print(warikan_kingaku)

    # 5. 各ユーザーの合計支払金額を計算
    #  5-1.Botサーバー内で保持されている各『対象ユーザー』『支払ったお金』データに対して、以下の処理をユーザ分繰り返す
    #      1.『対象ユーザ』のみのデータを抽出する
    #      2.該当データの『支払ったお金』を合計する
    #    3.『対象ユーザー』.『支払合計金額』の変数に保持
    #計算済

    # 6.各ユーザーの差額金額を計算する
    #  6-1. 『対象ユーザー』.『支払合計金額』と『合計金額』を使用して以下の計算を行い変数に値を格納する。
    #    『対象ユーザー』.『差額金額』=『対象ユーザー』.『支払合計金額』-『合計金額』
    #    『対象ユーザー』.『未精算金額』=『対象ユーザー』.『差額金額』
    sagaku_dict = {}
    for user in amount_dict:
        sagaku_dict[user] = warikan_kingaku - amount_dict[user]

        print(user)
        print(sagaku_dict[user])

    # 7.各ユーザーの精算結果を計算する
    #  7-1. 『対象ユーザー』.『支払合計金額』がプラスのユーザを『支払合計金額』で降順に並び替え順に格納しておく。
    #  7-2. 『対象ユーザー』.『支払合計金額』がマイナスのユーザを『支払合計金額』で昇順(マイナス値が大きい)に並び替え順に格納しておく。
    #  7-3. 精算を行う対象ユーザをピックアップ
    #     マイナスのユーザの昇順で一番上のものとプラスユーザの降順の一番上のものをピックアップ
    #  7-4.後続処理の判定（全員の『未精算金額』が０になるまで処理が繰り返される）
    #     IF(マイナスのユーザの『未精算金額』<> 0 and プラスのユーザの『未精算金額』<> 0 )なら
    #       //『支払合計金額』がマイナスのユーザに対して、以下の処理をおこなう
    #  7-5.精算処理
    #     IF(マイナスのユーザの『未精算金額』＋プラスのユーザの『未精算金額』＞＝ 0 )なら
    #       //精算結果の保持
    #       マイナスのユーザ.『精算結果』= ”プラスの『対象ユーザー』にマイナスのユーザ.『未精算金額』を払う”
    #       プラスのユーザ.『精算結果』= ”マイナスの『対象ユーザー』からマイナスのユーザ.『未精算金額』をもらう”
    #
    #       //未精算金額の計算と更新
    #       プラスのユーザ.『未精算金額』= プラスのユーザ.『未精算金額』- マイナスのユーザ.『未精算金額』
    #       マイナスのユーザ.『未精算金額』= 0
    #
    #     IF(マイナスのユーザの『支払合計金額』＋プラスのユーザの『支払合計金額』＜ 0 )なら
    #
    #          //精算結果の保持
    #       マイナスのユーザ.『精算結果』= ”プラスの『対象ユーザー』にプラスのユーザ.『未精算金額』を払う”
    #       プラスのユーザ.『精算結果』= ”マイナスの『対象ユーザー』からプラスのユーザ.『未精算金額』をもらう”
    #
    #      //未精算金額の計算と更新
    #       マイナスのユーザ.『未精算金額』= マイナスのユーザ.『未精算金額』- プラスのユーザ.『未精算金額』
    #       プラスのユーザ.『未精算金額』= 0
    #
    #       //上記計算をすべてのユーザに対しておこなう

    # 変数初期化
    pay_dict = {}
    for user in sagaku_dict:
        pay_dict[user] = {}

    # とりあえず送金回数最適化無視の送金額決定アルゴリズム
    for user1 in sagaku_dict:
        # print(user1)
        # print(sagaku_dict[user1])

        while(sagaku_dict[user1] != 0):
            if(sagaku_dict[user1] > 0):
                for user2 in sagaku_dict:
                    if(sagaku_dict[user2] < 0):
                        transfer = min(sagaku_dict[user1], -sagaku_dict[user2])
                        sagaku_dict[user1] -= transfer
                        sagaku_dict[user2] += transfer
                        pay_dict[user1].update({user2: -transfer})
                        pay_dict[user2].update({user1:  transfer})
                        # print(user1 + u'to' + user2 + u':' + str(transfer))
                    if(sagaku_dict[user1] == 0):
                        break;
            else:
                for user2 in sagaku_dict:
                    if(sagaku_dict[user2] > 0):
                        transfer = min(-sagaku_dict[user1], sagaku_dict[user2])
                        sagaku_dict[user1] += transfer
                        sagaku_dict[user2] -= transfer
                        pay_dict[user1].update({user2:  transfer})
                        pay_dict[user2].update({user1: -transfer})
                        # print(user2 + u'to' + user1 + u':' + str(transfer))
                    if(sagaku_dict[user1] == 0):
                        break;

    pprint.pprint(pay_dict)
    return pay_dict


if __name__ == "__main__":
    # create_dummy_json('warikan_dummy.json')
    load_json('warikan_dummy.json')

    for user in amount_dict:
        print user
        print get_amount(user)
        print get_payment(user)

    print get_total()
    print get_average()

    d = calc_warikan()

    # pprint(payment_dict)
    # pprint(d)

    pass
