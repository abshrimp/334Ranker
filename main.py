# MIT License
# Copyright (c) 2025 エイビー

# 2022年から修正を行いながら使用しているため、一部レガシー的な部分が存在します

import chromedriver_binary
import calendar
import datetime
import json
import os
import re
import requests
import base64
import sys
import threading
import time
import traceback
from collections import Counter, defaultdict

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver

from unofficial_twitter_client import android, web, oauth


TIME334 = [3, 34]       # 計測時刻
KEYWORD = "334"         # 検索ワード

PHP_URL = os.environ["PHP_URL"]             # phpが設置されているディレクトリを指定
MAIN_TOKENS = os.environ["MAIN_TOKENS"]     # 主アカウントの認証情報を、name$token$secretの形で（nameは小文字）
REP_TOKENS = os.environ["REP_TOKENS"]       # 返信用アカウントの認証情報を、name1$token1$secret1|name2$token2$secret2... の形で（nameは小文字）

HTML_URL = os.environ["HTML_URL"]           # dailyリザルト生成ページURL
HTML_URL2 = os.environ["HTML_URL2"]         # monthリザルト生成ページURL

clients = ['Twitter for iPhone',  'Twitter for Android',  'Twitter Web Client',  'TweetDeck',  'TweetDeck Web App',  'Twitter for iPad',  'Twitter for Mac',  'Twitter Web App',  'Twitter Lite',  'Mobile Web (M2)',  'Twitter for Windows',  'Janetter',  'Janetter for Android',  'Janetter Pro for iPhone',  'Janetter for Mac',  'Janetter Pro for Android',  'Tweetbot for iΟS',  'Tweetbot for iOS',  'Tweetbot for Mac',  'twitcle plus',  'ツイタマ',  'ツイタマ for Android',  'ツイタマ+ for Android',  'Sobacha',  'SobaCha',  'Metacha',  'MetaCha',  'MateCha',  'ツイッターするやつ',  'ツイッターするやつγ',  'ツイッターするやつγ pro',  'jigtwi',  'feather for iOS',  'hamoooooon',  'Hel2um on iOS',  'Hel1um Pro on iOS',  'Hel1um on iOS',  'undefined']

records_rank, today_result = {}, {}
past_records = []
today_joined = 0
joined_num = {"max_pt_rank": 0, "now_pt_rank": 0}
prepare_flag = False

main_account = MAIN_TOKENS.split("$")
rep_accounts2 = REP_TOKENS.split("|")
rep_accounts = []
for account in rep_accounts2:
    rep_accounts.append(account.split("$"))

def TweetIdTime(id):
    return datetime.datetime.fromtimestamp(((id >> 22) + 1288834974657) / 1000.0)

def request_php(url, data=None):
    for attempt in range(5):
        try:
            if data is not None:
                response = requests.post(
                    PHP_URL + url + ".php",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(data)
                )
                return response
            else:
                headers = {
                    "Accept-Encoding": "gzip, deflate"
                }
                response = requests.get(PHP_URL + url + ".php", headers=headers)

                return response.json()

        except Exception as e:
            print(f"request_php {attempt + 1} failed")

            if attempt < 4:
                print("Retrying in 60 seconds...")
                time.sleep(60)
            else:
                print("All php requests failed.")
                return None



account_switch = 0  # 返信用アカウント振り分け用カウンター

def reply(text, rep_id):
    global account_switch
    account_switch += 1
    index = account_switch % (len(rep_accounts) + 1)

    if index == len(rep_accounts):
        print(f"reply {main_account[0]} at {datetime.datetime.now()}")
        response = android.create_tweet(text, main_account[1], main_account[2], rep_id)
        if "errors" in response:
            print(response)

    else:
        print(f"reply {rep_accounts[index][0]} at {datetime.datetime.now()}")
        response = android.create_tweet(text, rep_accounts[index][1], rep_accounts[index][2], rep_id)

        if "errors" in response:    # エラーが発生した場合はメインアカウントで再投稿
            print(response)
            response = android.create_tweet(text, main_account[1], main_account[2], rep_id)


idlist = []  # 返信済みのツイートID

def receive(data):

    def get_kyui(pt):
        if pt < 500: rank = 'E'
        elif pt < 1000: rank = 'E+'
        elif pt < 1500: rank = 'D'
        elif pt < 2000: rank = 'D+'
        elif pt < 2500: rank = 'C'
        elif pt < 3000: rank = 'C+'
        elif pt < 3500: rank = 'B'
        elif pt < 4000: rank = 'B+'
        elif pt < 4500: rank = 'A'
        elif pt < 5000: rank = 'A+'
        elif pt < 5500: rank = 'S1'
        elif pt < 6000: rank = 'S2'
        elif pt < 6500: rank = 'S3'
        elif pt < 7000: rank = 'S4'
        elif pt < 7500: rank = 'S5'
        elif pt < 8000: rank = 'S6'
        elif pt < 8500: rank = 'S7'
        elif pt < 9000: rank = 'S8'
        elif pt < 9500: rank = 'S9'
        else: rank = 'RoR'
        return rank


    def get_rank(key, name):
        def s(key):
            return f"{round(d[key], 2):.2f}"

        if prepare_flag:
            return "ランキングは準備中です\\nしばらくお待ちください"
        
        if key in records_rank:
            d = records_rank[key]
            rep_text2 = f'\\n参考記録: {s("refer_pt")}' if d["now_pt"] != d["refer_pt"] else ""
            rank, rank2 = get_kyui(d["max_pt"]), get_kyui(d["now_pt"])
            
            return (
                f"{name}\\n\\n"
                f"級位: {rank}\\n"
                f"　最高pt: {s('max_pt')}\\n"
                f"　歴代: {d['max_pt_rank']} / {str(joined_num['max_pt_rank'])}\\n"
                f"　現在pt: {s('now_pt')} ({rank2}帯)\\n"
                f"　世界ランク: {d['now_pt_rank']} / {str(joined_num['now_pt_rank'])}{rep_text2}\\n"
                f"1s以内出場数: {str(d['count'])}\\n"
                f"自己ベスト: {d['best']} ({str(d['best_count'])}回)\\n"
                f"戦績: 🥇×{str(d['f'])} 🥈×{str(d['s'])} 🥉×{str(d['t'])} 📋×{str(d['rankin'])}"
            )
        
        return (
            f"{name}\\n\\n"
            f"最高pt: -\\n"
            f"歴代: - / {str(joined_num['max_pt_rank'])}\\n"
            f"現在pt: -\\n"
            f"世界ランク: - / {str(joined_num['now_pt_rank'])}\\n"
            f"1s以内出場数: 0\\n"
            f"自己ベスト: -\\n"
            f"戦績: 🥇×0 🥈×0 🥉×0 📋×0"
        )


    def has_rank(key, name, data):
        """ランクを要求しているか判定"""
        """return ランク返信文章 or False"""
        
        text = data["full_text"].lower()
        mentions = data["entities"]["user_mentions"]
        
        for user in mentions:
            text = text.replace("@" + user["screen_name"].lower(), "")
        
        if any(x in text for x in ["ランク", "ﾗﾝｸ", "らんく", "rank", "ランキング", "ﾗﾝｷﾝｸﾞ"]):
            return get_rank(key, name)
        
        if any(x in text for x in ["順位", "じゅんい", "ジュンイ", "ｼﾞｭﾝｲ"]):
            return get_result(key, name)
        
        return False


    def get_result(key, name):
        """当日の結果返信文章生成"""
        
        previous = datetime.datetime.now() - datetime.timedelta(hours=TIME334[0], minutes=TIME334[1] - 1)
        
        if prepare_flag:
            return "ランキングは準備中です\\nしばらくお待ちください"
        
        if key in today_result:
            return (
                f"{name}\\n\\n"
                f"{previous.date().strftime('%Y/%m/%d')}の{KEYWORD}結果\\n"
                f"result: +{today_result[key][1]} [sec]\\n"
                f"rank: {str(today_result[key][0])} / {str(today_joined)}"
            )
        
        return (
            f"{name}\\n\\n"
            f"{previous.date().strftime('%Y/%m/%d')}の{KEYWORD}結果\\n"
            f"result: DQ\\n"
            f"rank: DQ / {str(today_joined)}"
        )

    def follow_request(data, mentions=[]):
        """フォローリクエスト"""
        """return フォローした or ランク返信文章 or False"""
        
        legacy = data["user"]
        user_id = legacy["id_str"]
        text = data["full_text"].lower()
        
        for mention in mentions:
            text = text.replace("@" + mention["screen_name"].lower(), "")
        
        if any(x in text for x in ["ふぉろー", "フォロー", "follow", "ふぉろば", "フォロバ"]):
            if any(x in text for x in ["してもいいですか", "しても大丈夫ですか", "させていただきました"]):  # エロスパムを排除
                return False
            
            try:
                if "following" not in legacy and "followed_by" not in legacy:
                    user_data = android.get_user(user_id, main_account[1], main_account[2])
                    legacy = user_data["data"]["user_result"]["result"]["legacy"]
                
                if "following" in legacy and legacy["following"]:
                    return "既にフォローしています"
                
                if "followed_by" in legacy and legacy["followed_by"]:
                    response = android.create_follow(user_id, main_account[1], main_account[2])
                    if "errors" in response:
                        return 'エラーが発生しました🙇\\n時間をおいてもう一度お試しください'
                    return "フォローしました"
                else:
                    return f"{KEYWORD}Rankerをフォローしてからお試しください"
                    
            except Exception as e:
                traceback.print_exc()
                return 'エラーが発生しました🙇\\n時間をおいてもう一度お試しください'
        else:
            return has_rank(user_id, "@ " + legacy["screen_name"], data)
        
    def tweet_time(id_str):
        d = TweetIdTime(int(id_str))
        return f"ツイート時刻：{d.hour:02d}:{d.minute:02d}:{d.second:02d}.{int(d.microsecond / 1000):03d}"


    # follow_request -> has_rank -> get_rank -> get_result -> (tweet_time)
    global idlist
    rep_accounts_ids = [main_account[1].split("-")[0]] + [account[1].split("-")[0] for account in rep_accounts]

    user = data["user"]
    mentions = data["entities"]["user_mentions"]

    if user["id_str"] not in rep_accounts_ids and data["id_str"] not in idlist:
        rep_text = False
        idlist.append(data["id_str"])

        if "in_reply_to_status_id_str" not in data or data["in_reply_to_status_id_str"] == None:
            rep_text = follow_request(data, mentions)  # リプライ先がリプライでない場合 検索にかかったもの全て対象
            if not rep_text:
                rep_text = tweet_time(data["id_str"])

        else:  # リプライ先がリプライの場合
            if data["in_reply_to_user_id_str"] in rep_accounts_ids:
                rep_text = follow_request(data, mentions)  # Rankerへのリプライの場合

            else:  # Ranker以外へのリプライの場合
                user_id = data["in_reply_to_user_id_str"]
                text_range = data["display_text_range"]
                flag = False

                for user2 in mentions:
                    if user2["id_str"] in rep_accounts_ids and text_range[0] <= user2["indices"][0] and user2["indices"][1] <= text_range[1]:
                        flag = True
                if flag:
                    user_name = "@ " + data["in_reply_to_screen_name"]
                    rep_text = has_rank(user_id, user_name, data)
                    if not rep_text:
                        rep_text = tweet_time(data["in_reply_to_status_id_str"])

        if rep_text:
            print(user["name"])
            threading.Thread(target=reply, args=(rep_text, data["id_str"],)).start()


def get_mention_from_notion(since, end):
    """通知欄からメンションを取得"""

    cursor = None
    screen_names = [main_account[0]] + [account[0] for account in rep_accounts]

    def loop():
        nonlocal cursor

        response = web.get_mentions_web(main_account[1], main_account[2], cursor)
        instructions = response['data']['viewer_v2']['user_results']['result']['notification_timeline']['timeline']['instructions']

        for instruction in instructions:
            if instruction['type'] != "TimelineAddEntries":
                continue

            for tweet in instruction['entries']:
                if 'cursor-top' in tweet['entryId']:
                    cursor = tweet['content']['value']
                    
                if "itemContent" not in tweet['content']:
                    continue
                
                if tweet['content']['itemContent']['itemType'] == "TimelineTweet":
                    result = tweet['content']['itemContent']['tweet_results']['result']
                    legacy = result['legacy']
                    if all(str not in legacy['full_text'].lower() for str in screen_names): continue
                    if since <= TweetIdTime(int(legacy['id_str'])) < end:
                        legacy['user'] = result['core']['user_results']['result']['core']
                        legacy['user']['id_str'] = result['core']['user_results']['result']['rest_id']
                        threading.Thread(target=receive, args=(legacy,)).start()

    while datetime.datetime.now() < since: time.sleep(0.01)
    counter = 0
    while datetime.datetime.now() <= end:
        start = since + datetime.timedelta(seconds = counter * 1)
        while datetime.datetime.now() < start: time.sleep(0.01)
        threading.Thread(target=loop).start()
        counter += 1


def make_world_rank():
    """級位ポイント計算"""

    def sort_and_rank(input, output, records):
        """ソートして順位をつける"""

        global joined_num
        sorted_items = sorted(records.items(), key=lambda item: item[1][input], reverse=True)
        current_rank = 1
        previous_value = None
        index = 0

        for i, (key, value) in enumerate(sorted_items):
            if value[input] == 0:
                records[key][output] = '-'
                continue
            index += 1
            if value[input] != previous_value: current_rank = index
            records[key][output] = str(current_rank)
            previous_value = value[input]
        joined_num[output] = index


    def time_to_point(date, result):
        """タイムをポイントに変換"""

        days = (datetime.datetime.now() - date).days
        b = 10000 * 2 ** (-10 * float(result))
        if days >= 30: b *= (91 - days) / 61
        return b


    user_data = defaultdict(lambda: {'valid': [], 'all': []})
    for entry in past_records:
        userid, date, value, source = entry
        transformed_value = time_to_point(date, value)
        user_data[userid]['all'].append(transformed_value)
        if source in clients: user_data[userid]['valid'].append(transformed_value)

    def get_top_10(values):
        top_values = sorted(values, reverse=True)[:10]
        while len(top_values) < 10:
            top_values.append(0)
        return top_values

    top_values = {}
    for userid, entries in user_data.items():
        top_valid_values = get_top_10(entries['valid'])
        top_all_values = get_top_10(entries['all'])
        top_values[userid] = {
            'valid': top_valid_values,
            'all': top_all_values
        }

    for id in records_rank:
        if id in top_values:
            records_rank[id]['now_pt'] = sum(top_values[id]['valid']) / 10
            if records_rank[id]['max_pt'] < records_rank[id]['now_pt']: records_rank[id]['max_pt'] = records_rank[id]['now_pt']
            records_rank[id]['refer_pt'] = sum(top_values[id]['all']) / 10
        else:
            records_rank[id]['now_pt'] = 0
            records_rank[id]['refer_pt'] = 0

    sort_and_rank('max_pt', 'max_pt_rank', records_rank)
    sort_and_rank('now_pt', 'now_pt_rank', records_rank)


def make_ranking(results_dict_arr, _driver):
    """当日分のランキングの作成"""

    prepare_flag2 = True

    def make_month_rank():
        month_record, month_source = {}, {}
        n = datetime.datetime.now()
        month_days = calendar.monthrange(n.year, n.month)[1]
        response = request_php('get')

        for record in response:
            record_time = datetime.datetime.strptime(record['date'], '%Y-%m-%d') + datetime.timedelta(hours=TIME334[0], minutes=TIME334[1])
            days = (datetime.datetime.now() - record_time).days
            if days < month_days and record['source'] in clients:
                id = record['userid']
                if id not in month_record:
                    month_record[id], month_source[id] = [], []
                pt = 10000 * 2 ** (-10 * float(record['result']))
                if len(month_record[id]) < 10:
                    month_record[id].append(pt)
                elif min(month_record[id]) < pt:
                    month_record[id].remove(min(month_record[id]))
                    month_record[id].append(pt)
                month_source[id].append(record['source'])

        month_data = []
        for id in month_record:
            month_data.append([id, sum(month_record[id]) / 10])
        sorted_items = sorted(month_data, key=lambda x: x[1], reverse=True)
        rankdata = []
        current_rank = 1
        previous_value = None
        index = 0

        for value in sorted_items:
            index += 1
            if index > 30: break
            if value[1] != previous_value: current_rank = index
            counter = Counter(month_source[value[0]])
            try:
                response = android.get_user(value[0], main_account[1], main_account[2])
                legacy = response['data']['user_result']['result']['legacy']
                name = legacy['name']
                if name == '': name = '@' + legacy['screen_name']
                rankdata.append([current_rank, legacy['profile_image_url_https'], legacy['name'], value[1], len(month_source[value[0]]), counter.most_common(1)[0][0]])
                time.sleep(1)
            except:
                rankdata.append([current_rank, '', 'unknown', value[1], len(month_source[value[0]]), counter.most_common(1)[0][0]])
            previous_value = value[1]

        _driver.get(HTML_URL2)
        wait = WebDriverWait(_driver, 20).until(EC.alert_is_present())
        Alert(_driver).accept()
        for _ in range(5):
            try:
                _driver.execute_script('document.getElementById("input").value = arguments[0]; start();', str(rankdata))
                wait = WebDriverWait(_driver, 20).until(EC.alert_is_present())
            except Exception as e:
                traceback.print_exc()
                _driver.get(HTML_URL2)
                time.sleep(1)
            else:
                Alert(_driver).accept()
                bin = _driver.execute_script('return window.res')
                print("POST RANK2 :")
                oauth.tweet_with_img("This month's top 30", base64.b64decode(bin))
                _driver.quit()
                break

    def make_img(tweets):
        """ランキング画像の生成とアップロード"""

        for _ in range(5):
            try:
                _driver.execute_script('document.getElementById("input").value = arguments[0]; start();', tweets)
                wait = WebDriverWait(_driver, 20).until(EC.alert_is_present())
            except Exception as e:
                traceback.print_exc()
                _driver.get(HTML_URL)
                time.sleep(1)
            else:
                Alert(_driver).accept()
                bin = _driver.execute_script('return window.res')
                print("POST RANK :")
                oauth.tweet_with_img("Today's top 30", base64.b64decode(bin))

                next_day = datetime.datetime.now() + datetime.timedelta(days=1)
                if next_day.day == 1:
                    while prepare_flag2:
                        time.sleep(1)
                    time.sleep(1)
                    make_month_rank()
                else:
                    _driver.quit()
                break


    #生データを扱いやすい形に変換
    global records_rank, today_result, today_joined, prepare_flag
    now = datetime.datetime.now()
    today_str = now.date().strftime('%Y-%m-%d')
    time_334 = datetime.datetime.combine(now.date(), datetime.time(TIME334[0], TIME334[1]))
    joined_users = ['1173558244607852545']  ### 除外リスト
    results_for_img = []
    update_records_rank = []
    update_past_records = []
    results_dict_arr = sorted(results_dict_arr, key=lambda x: int(x['id_str']))
    current_rank = 1
    today_joined = 0
    previous_value = None

    for item in results_dict_arr:
        if item['text'] == KEYWORD and item['user']['id_str'] not in joined_users:
            joined_users.append(item['user']['id_str'])
            result_time = (TweetIdTime(int(item['id_str'])) - time_334).total_seconds()
            if 0 <= result_time < 1:
                result_str = '{:.3f}'.format(result_time)

                img_src = 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'
                if item['user']['profile_image_url_https'] != '': img_src = item['user']['profile_image_url_https']

                if item['source'] == 'undefined':
                    response = web.get_tweet(item['id_str'], main_account[1], main_account[2])
                    item['source'] = response["data"]["threaded_conversation_with_injections_v2"]["instructions"][0]["entries"][-1]["content"]["itemContent"]["tweet_results"]["result"]["source"]
                match = re.search(r'<a[^>]*>([^<]*)</a>', item['source'])
                source = match.group(1) if match else item['source']

                id = item['user']['id_str']

                results_for_img.append([
                    img_src,
                    item['user']['name'],
                    result_str,
                    source,
                    item['id_str'],
                    '@' + item['user']['screen_name'],
                    id
                ])

                today_joined += 1
                if result_str != previous_value: current_rank = today_joined
                previous_value = result_str
                today_result[id] = [current_rank, result_str]
                if id not in records_rank:
                    records_rank[id] = {
                        'best': result_str,
                        'best_count': 0,
                        'max_pt': 0.0,
                        'count': 0,
                        'f': 0,
                        's': 0,
                        't': 0,
                        'rankin': 0
                    }
                records_rank[id]['count'] += 1
                if result_time < float(records_rank[id]['best']):
                    records_rank[id]['best'] = result_str
                    records_rank[id]['best_count'] = 1
                elif result_time == float(records_rank[id]['best']):
                    records_rank[id]['best_count'] += 1
                    
                if current_rank == 1:
                    records_rank[id]['f'] += 1
                    threading.Thread(
                        target=oauth.quote_tweet,
                        args=("Today's winner", item['user']['screen_name'], item['id_str'])
                    ).start()
                elif current_rank == 2:
                    records_rank[id]['s'] += 1
                elif current_rank == 3:
                    records_rank[id]['t'] += 1

                if current_rank <= 30: records_rank[id]['rankin'] += 1

                update_list = list(records_rank[id].values())[:8]
                update_list.insert(0, id)
                update_records_rank.append(update_list)

                past_records.append([id, now, result_str, source])
                update_past_records.append([id, today_str, result_str, source]) #JSONにできるよう文字列に

    print(str(results_for_img))
    threading.Thread(target=make_img, args=(str(results_for_img),)).start()
    
    make_world_rank()
    for update_record in update_records_rank:
        update_record[3] = records_rank[update_record[0]]['max_pt']

    prepare_flag = False

    response = request_php('add_rank', update_records_rank)
    print("Response:", response.status_code, response.text)
    response = request_php('add', update_past_records)
    print("Response:", response.status_code, response.text)

    prepare_flag2 = False


def get334(oauth_token, token_secret, search_only, func):
    now = datetime.datetime.now()
    time1 = datetime.datetime(now.year, now.month, now.day, TIME334[0], TIME334[1], 59) - datetime.timedelta(minutes=1)
    time2 = datetime.datetime(now.year, now.month, now.day, TIME334[0], TIME334[1], 1)
    out = []
    out2 = []
    end_flag = True

    count = 0
    def final():
        nonlocal count, out2, end_flag
        count += 1
        if count >= (1 if search_only else 3):
            out.sort(key=lambda x: x['index'])
            ids = []
            for item in out:
                if item['id_str'] not in ids:
                    out2.append(item)
                    ids.append(item['id_str'])
            print("GET334 COMPLETE  search_only:", search_only)
            end_flag = False


    def add_arr(res, arr, entry_id):
        legacy = res['legacy']
        if TweetIdTime(int(legacy['id_str'])) < time1:
            if "home" in entry_id:
                return True
            else:
                final()
                return False

        legacy['text'] = legacy['full_text']
        if legacy['text'] != KEYWORD: return True

        legacy['source'] = res['source']
        legacy['index'] = (int(legacy['id_str']) >> 22) + 1288834974657
        legacy['user'] = res['core']['user_results']['result']['legacy']
        legacy['user']['id_str'] = legacy['user_id_str']
        legacy['user']['profile_image_url_https'] = res['core']['user_results']['result']['avatar']['image_url']
        legacy['user']['name'] = res['core']['user_results']['result']['core']['name']
        legacy['user']['screen_name'] = res['core']['user_results']['result']['core']['screen_name']
        arr.append(legacy)
        return True


    def get_timeline(cursor = None):
        nonlocal out
        print("GET334 get_timeline  search_only:", search_only)
        try:
            data = web.latest_timeline_web(oauth_token, token_secret, cursor)
            entries = data['data']['home']['home_timeline_urt']['instructions'][0]['entries']

            for entry in entries:
                entry_id = entry['entryId']
                if "bottom" in entry_id:
                    get_timeline(entry['content']['value'])
                    return
                
                try:
                    if "promoted" in entry_id or "cursor" in entry_id: continue
                    if "home" in entry_id:
                        res = entry['content']['items'][0]['item']['itemContent']['tweet_results']['result']
                    else:
                        res = entry['content']['itemContent']['tweet_results']['result']
                    if "tweet" in res:
                        res = res['tweet']

                    if not add_arr(res, out, entry_id): return

                except Exception as e:
                    print(e)

            final()

        except Exception as e:
            traceback.print_exc()
            final()


    def get_search(cursor = None):
        nonlocal out
        print("GET334 get_search  search_only:", search_only)
        screen_names = f'-from:{main_account[0]} ' + ' '.join([f'-from:{account[0]}' for account in rep_accounts])
        text = f"{KEYWORD} -filter:retweets -filter:quote {screen_names} since:{time1.strftime('%Y-%m-%d_%H:%M:%S_JST')} until:{time2.strftime('%Y-%m-%d_%H:%M:%S_JST')}"
        try:
            flag = True
            data = web.search_timeline_web(text, oauth_token, token_secret, cursor)
            instructions = data['data']['search_by_raw_query']['search_timeline']['timeline']['instructions']

            for instruction in instructions:
                entries = []
                if 'entries' in instruction:
                    entries = instruction['entries']
                elif 'entry' in instruction:
                    entries = [instruction['entry']]
                else:
                    continue

                for entry in entries:
                    entry_id = entry['entryId']
                    if "bottom" in entry_id:
                        if flag:
                            final()
                        else:
                            get_search(entry['content']['value'])
                        return
                    
                    try:
                        if "promoted" in entry_id or "cursor" in entry_id :
                            continue

                        flag = False
                        res = entry['content']['itemContent']['tweet_results']['result']
                        if "tweet" in res:
                            res = res['tweet']
                        if not add_arr(res, out, entry_id): return

                    except Exception as e:
                        print(e)
                    
            final()

        except Exception as e:
            traceback.print_exc()
            final()


    get_time = time2 + datetime.timedelta(seconds=1)
    while datetime.datetime.now() < get_time: time.sleep(0.01)
    print("GET334 START  search_only:", search_only)
    if search_only:
        threading.Thread(target = get_search).start()
    else:
        threading.Thread(target = get_timeline).start()
        threading.Thread(target = get_search).start()
        time.sleep(2)
        threading.Thread(target = get_search).start()
    while end_flag:
        time.sleep(1)
    func(out2)


def main334(_driver):

    result = []
    count = 0
    def func(arr):
        nonlocal result, count
        result = result + arr
        count += 1
        if count >= 1 + len(rep_accounts):
            make_ranking(result, _driver)

    threading.Thread(target=get334, args=(main_account[1], main_account[2], False, func,)).start()
    for rep_account in rep_accounts:
        threading.Thread(target=get334, args=(rep_account[1], rep_account[2], True, func,)).start()


def notice():
    global today_result, prepare_flag
    today = datetime.datetime.now().date()
    notice_time = datetime.datetime.combine(today, datetime.time(TIME334[0], TIME334[1])) - datetime.timedelta(minutes=2)
    while datetime.datetime.now() < notice_time: time.sleep(5)
    today_result = {}
    prepare_flag = True
    print("NOTICE :")
    try:
        oauth.tweet_by_oauth(f"{KEYWORD}観測中 ({today.strftime('%Y/%m/%d')})")
    except Exception as e:
        traceback.print_exc()

    _driver = {}
    
    for _ in range(5):
        try:
            options=Options()
            #options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument('--disable-dev-shm-usage')
            _driver = webdriver.Chrome(options = options)
            _driver.set_window_size(589, 1)
            _driver.get(HTML_URL)
            wait = WebDriverWait(_driver, 20).until(EC.alert_is_present())
            Alert(_driver).accept()
        except Exception as e:
            traceback.print_exc()
            _driver.quit()
            time.sleep(5)
        else:
            main334(_driver)
            break

def get_rank_data():
    global past_records, today_result, today_joined, records_rank
    today_unsorted = []
    response = request_php('get')
    for record in response:
        record_time = datetime.datetime.strptime(record['date'], '%Y-%m-%d') + datetime.timedelta(hours=TIME334[0], minutes=TIME334[1])
        days = (datetime.datetime.now() - record_time).days
        if days <= 91: past_records.append([record['userid'], record_time, record['result'], record['source']])
        if days == 0: today_unsorted.append([record['userid'], record['result']])
    today_unsorted = sorted(today_unsorted, key=lambda x: float(x[1]))
    current_rank = 1
    today_joined = 0
    previous_value = None
    for record in today_unsorted:
        today_joined += 1
        if record[1] != previous_value: current_rank = today_joined
        today_result[record[0]] = [current_rank, record[1]]
        previous_value = record[1]
    
    response = request_php('get_rank')
    for record in response:
        id = record['userid']
        del record['userid']
        record['max_pt'] = float(record['max_pt'])
        records_rank[id] = {key: int(value) if key not in ['best', 'max_pt'] else value for key, value in record.items()}

    make_world_rank()


def main():

    now = datetime.datetime.now()
    base_time = datetime.datetime(now.year, now.month, now.day, TIME334[0], TIME334[1], 0) - datetime.timedelta(minutes=10)     #10分前より開始

    times = []
    for i in range(6):
        start_time = base_time + datetime.timedelta(hours=i * 4)
        end_time = start_time + datetime.timedelta(hours=4)
        times.append([start_time, end_time])

    times[-1][1] = base_time + datetime.timedelta(days=1)
    times.append([base_time + datetime.timedelta(days=1), base_time + datetime.timedelta(days=1)])

    for i in range(len(times)):
        if now < times[i][0]:

            print('START')

            get_rank_data()
            print('LOADED RANK')

            if len(sys.argv) != 1:
                if sys.argv[1] == "recount":
                    print('RECOUNT MODE')
                    notice()
                    return

                print('TEST MODE')
                start_time = datetime.datetime.now().replace(microsecond = 0) + datetime.timedelta(seconds=1)
                end_time = times[i][0]
            else:
                start_time = times[i][0]
                end_time = times[i][1]
            print(start_time, end_time)

            threading.Thread(target = get_mention_from_notion, args=(start_time, end_time,)).start()
            
            if start_time < datetime.datetime(now.year, now.month, now.day, TIME334[0], TIME334[1], 0) < end_time:
                print('334MODE')
                notice()
                
            break

main()
         