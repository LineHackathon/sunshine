#!/usr/bin/python
# -*- coding: utf-8 -*-

from pprint import pprint

def calc_warikan(amounts):
    members = amounts.keys()
    return calc_warikan2(members, amounts)

def calc_warikan2(members, amounts, additionals={}, rates={}):
    total = 0
    for member in amounts:
        total += amounts[member]
    for member in additionals:
        total -= additionals[member]
    # print total

    denomi = 0.0
    for member in members:
        denomi += rates.get(member, 1.0)
    print denomi

    # average = total // len(members)
    # remainder = total % len(members)
    average = int(total // denomi)
    remainder = total
    for member in members:
        remainder -= int(average * rates.get(member, 1.0))
    # remainder = total % denomi
    print average
    print remainder
    # print temp
    # return;

    # 総額計算
    totals={}
    for i, member in enumerate(members):
        totals[member] = int(average * rates.get(member, 1.0))
        totals[member] += additionals.get(member,0)
        if(i < remainder):
            totals[member] += 1
    print totals

    # 渡す額，貰う額を決定
    gives={}
    takes={}
    transfer_total = 0
    for member in members:
        diff = totals[member] - amounts.get(member, 0)
        # print diff
        if(diff > 0):
            gives[member] = diff
            takes[member] = 0
        else:
            gives[member] = 0
            takes[member] = -diff
        transfer_total += abs(diff)
    # print gives
    # print takes
    # print transfer_total
    # return

    # お金のやり取りを計算
    transfer_list = []
    while(transfer_total != 0):
        give_max_member = max(gives.items(), key=lambda x:x[1])[0]
        take_max_member = max(takes.items(), key=lambda x:x[1])[0]
        transfer = min(gives[give_max_member], takes[take_max_member])
        transfer_total -= transfer * 2
        gives[give_max_member] -= transfer
        takes[take_max_member] -= transfer
        transfer_list.append({'from': give_max_member, 'to': take_max_member, 'amount': transfer})
        # print transfer_total
    # print transfer_list

    return transfer_list


if __name__ == "__main__":
    # レンタカー ：9,800円（ユーザーAが自宅近くのレンタカー屋でカード支払い）
    # ガソリン代 ：7,600円（ユーザーBがガソリンスタンドでカード支払い）
    # 高速道路料金 ：7,400円（ユーザーCのETCカードで支払い）
    # フリーパス：17,600円（ユーザーDがWeb予約で事前決済）
    members = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    amounts = {
        'A': 9800,
        'B': 7600,
        'C': 7400,
        'D': 17600,
    }
    additionals = {
        'H': 2000,
    }
    rates = {
        'F': 1.1,
    }
    transfer_list = calc_warikan2(members, amounts, additionals, rates)
    pprint(transfer_list)

    amounts = {
        'A': 9800,
        'B': 7600,
        'C': 7400,
        'D': 17600,
        'E': 0,
        'F': 0,
        'G': 0,
        'H': 0,
    }
    transfer_list = calc_warikan(amounts)
    pprint(transfer_list)
