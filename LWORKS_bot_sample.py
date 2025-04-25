import json
import requests
import jwt
import cryptography
from datetime import datetime
from flask import Flask, request, jsonify
import os

# テナント情報（あなたの情報に書き換えてください）
APIKEY = 'APIKEY'
SERVER_CKEY = 'SERVER CONSUMER KEY'
SERVERID = "Server ID(ID 登録タイプの方)"
PRIVKEY = '認証キーファイルのパス'
BOT_NO = 'BOT番号'  # 例: 12345

# グローバル変数にトークンを保持（30分有効）
SERVER_TOKEN = ''

# JWT から server token の生成
def gettoken(ServerId, PrivateKey):
    crnttime = int(datetime.now().strftime('%s'))
    exptime = crnttime + 1800

    claimset = {
        "iss": ServerId,
        "iat": crnttime,
        "exp": exptime
    }

    key = open(PrivateKey).read()
    lw_jwt = jwt.encode(claimset, key, algorithm='RS256')

    url = 'https://authapi.worksmobile.com/b/' + APIKEY + '/server/token'
    header = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'charset': 'utf-8'
    }
    payload = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': lw_jwt.decode('utf-8') if isinstance(lw_jwt, bytes) else lw_jwt
    }
    r = requests.post(url, headers=header, params=payload)
    if r.status_code == 200:
        token_data = json.loads(r.text)
        return token_data['access_token']
    else:
        print("Token取得失敗:", r.text)
        return None

# メッセージ送信
def sendmsg(bot_no, target_id, message, server_token):
    url = 'https://apis.worksmobile.com/' + APIKEY + '/message/sendMessage/v2'
    header = {
        'consumerKey': SERVER_CKEY,
        'Authorization': 'Bearer ' + server_token,
        'Content-Type': 'application/json'
    }

    payload = {
        "botNo": bot_no,
        "accountId": target_id,
        "content": {
            "type": "text",
            "text": message
        }
    }

    r = requests.post(url, headers=header, data=json.dumps(payload))
    if r.status_code == 200 and r.json().get("code") == 200:
        print("送信成功:", r.json())
        return r.json()
    else:
        print("送信失敗:", r.text)
        return None


# Flaskアプリ設定
app = Flask(__name__)

@app.route('/')
def index():
    return "LINE WORKS Bot is running."

@app.route('/callback', methods=['POST'])
def callback():
    data = request.json
    print("受信データ:", data)

    try:
        content = data['content']
        user_message = content['text']
        account_id = data['source']['accountId']

        print("User Message:", user_message)

        if 'お疲れ様' in user_message:
            sendmsg(BOT_NO, account_id, '今日もお疲れ様でした！', SERVER_TOKEN)

    except Exception as e:
        print("受信メッセージの処理エラー:", e)

    return "OK"


if __name__ == '__main__':
    # 起動時にトークンを取得
    SERVER_TOKEN = gettoken(SERVERID, PRIVKEY)
    if not SERVER_TOKEN:
        print("サーバートークンの取得に失敗しました。")
        exit(1)

    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
