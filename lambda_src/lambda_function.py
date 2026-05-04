import json
import os
import urllib.request
import urllib.error
import boto3
from datetime import datetime, timezone

LINE_ACCESS_TOKEN = os.environ["LINE_ACCESS_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TABLE_NAME = os.environ["TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

CHARACTERS = [
    "神",
    "悪魔",
    "未来の自分",
    "過去の自分",
    "好きな人(男子)",
    "好きな人(女子)",
    "あの頃の先輩",
    "やる気0%の神",
    "犬",
    "猫",
    "常にあなたを見守ってる誰か",
    "開発者"
]


def lambda_handler(event, context):
    print("event:", json.dumps(event, ensure_ascii=False))

    try:
        body = json.loads(event.get("body", "{}"))
        events = body.get("events", [])

        if not events:
            return response_200("No events")

        for line_event in events:
            handle_line_event(line_event)

        return response_200("OK")

    except Exception as e:
        print("error:", str(e))
        return {
            "statusCode": 500,
            "body": "Internal Server Error"
        }


def handle_line_event(line_event):
    if line_event.get("type") != "message":
        print("not message event:", line_event.get("type"))
        return

    message = line_event.get("message", {})
    reply_token = line_event.get("replyToken")
    user_id = line_event.get("source", {}).get("userId")

    if not reply_token:
        print("no replyToken")
        return

    if message.get("type") != "text":
        reply_to_line(
            reply_token,
            "🔮 テキストで送ってくれたら占うぞ。スタンプでは運命が読めぬ。"
        )
        return

    user_message = message.get("text", "").strip()

    display_name = None

    if user_id:
        display_name = get_display_name(user_id)
        update_user_profile(user_id, user_message, display_name)

    if "占って" in user_message:
        reply_with_quick_reply(reply_token)
        return

    if user_message in CHARACTERS:
        reply_text = generate_fortune(user_message, display_name)

        if user_id:
            save_last_character(user_id, user_message)
            save_fortune_history(user_id, user_message, reply_text)

        reply_to_line(reply_token, reply_text)
        return

    reply_to_line(
        reply_token,
        '🔮 占いをご希望なら「占って」と送るのだ。\nそれ以外の言葉では、水晶がただの丸い石になる。'
    )


def get_display_name(user_id):
    profile = get_line_profile(user_id)

    if not profile:
        return None

    return profile.get("displayName")


def get_line_profile(user_id):
    url = f"https://api.line.me/v2/bot/profile/{user_id}"

    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }

    req = urllib.request.Request(
        url,
        headers=headers,
        method="GET"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        print("LINE profile HTTPError:", e.code)
        print(e.read().decode("utf-8"))
        return None

    except Exception as e:
        print("LINE profile error:", str(e))
        return None


def update_user_profile(user_id, user_message, display_name):
    now = datetime.now(timezone.utc).isoformat()

    try:
        table.update_item(
            Key={
                "userId": f"USER#{user_id}",
                "sortKey": "PROFILE"
            },
            UpdateExpression="""
                SET updated_at = :updated_at,
                    last_message = :last_message,
                    display_name = :display_name
                ADD message_count :inc
            """,
            ExpressionAttributeValues={
                ":updated_at": now,
                ":last_message": user_message,
                ":display_name": display_name if display_name else "名無しの旅人",
                ":inc": 1
            }
        )
    except Exception as e:
        print("DynamoDB update_user_profile error:", str(e))


def save_last_character(user_id, character):
    now = datetime.now(timezone.utc).isoformat()

    try:
        table.update_item(
            Key={
                "userId": f"USER#{user_id}",
                "sortKey": "PROFILE"
            },
            UpdateExpression="""
                SET last_character = :last_character,
                    last_fortune_at = :last_fortune_at
            """,
            ExpressionAttributeValues={
                ":last_character": character,
                ":last_fortune_at": now
            }
        )
    except Exception as e:
        print("DynamoDB save_last_character error:", str(e))


def save_fortune_history(user_id, character, fortune_text):
    now = datetime.now(timezone.utc).isoformat()

    try:
        table.put_item(
            Item={
                "userId": f"USER#{user_id}",
                "sortKey": f"HISTORY#{now}",
                "character": character,
                "fortune_text": fortune_text,
                "created_at": now
            }
        )
    except Exception as e:
        print("DynamoDB save_fortune_history error:", str(e))


def reply_with_quick_reply(reply_token):
    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }

    items = [
        ("👼 神", "神"),
        ("😈 悪魔", "悪魔"),
        ("👫 未来の自分", "未来の自分"),
        ("🧒 過去の自分", "過去の自分"),
        ("💘 好きな人(男子)", "好きな人(男子)"),
        ("💘 好きな人(女子)", "好きな人(女子)"),
        ("👋 あの頃の先輩", "あの頃の先輩"),
        ("⛩️ やる気0%の神", "やる気0%の神"),
        ("🐶 犬", "犬"),
        ("😺 猫", "猫"),
        ("⛅️ 常にあなたを見守ってる誰か", "常にあなたを見守ってる誰か"),
        ("💻 開発者", "開発者"),
    ]

    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": "🔮 誰に占わせる？",
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": label,
                                "text": text
                            }
                        }
                        for label, text in items
                    ]
                }
            }
        ]
    }

    send_line_request(url, headers, data)


def generate_fortune(character, display_name):
    url = "https://api.openai.com/v1/chat/completions"

    character_prompt = get_character_prompt(character)
    user_name = display_name if display_name else "名無しの旅人"

    prompt = f"""
あなたは「{character}」目線で占いをします。

占う相手の名前：
{user_name}

キャラ設定：
{character_prompt}

条件：
- 日本語
- キャラに合った口調にする
- 冒頭か「あなたに言いたいこと」で、自然に「{user_name}よ、」のように名前を呼ぶ
- ただし毎回くどくならないように自然に入れる
- ネタよりで、辛口で笑える
- 最後にちょっと前向きにする
- 270文字ぐらい
- ●の項目ごとに改行を入れて読みやすく
- 運勢は【神吉, 大吉, 小吉, 吉, 謎吉, 凶, 大凶, カス凶】
- でる割合は神吉は15%, 大吉は15%, 小吉は15%, 吉は15%, 謎吉は10%, 凶は10%, 大凶は10%, カス凶は10%
- 運勢によって他の出力の具合も調節して
- あなたに言いたいこと：は分量多め

出力フォーマット：
🔮 占い結果

●運勢：
●ひとこと：
●ラッキーアイテム：
●ラッキー行動：
●本日の何か良いことある率：
●今日の分岐点：
●今日の無駄なアドバイス：
●あなたに言いたいこと：
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "あなたはユーモアのある占い師です。短く、自然で、LINEで読みやすい文章を書きます。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.9,
        "max_tokens": 500
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            response_body = json.loads(res.read().decode("utf-8"))
            return response_body["choices"][0]["message"]["content"]

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print("OpenAI API HTTPError:", e.code, error_body)
        return "🔮 占いの水晶が曇っております。少し時間を置いてもう一度どうぞ。"

    except Exception as e:
        print("OpenAI API error:", str(e))
        return "🔮 星の通信に失敗しました。もう一度送ってみてください。"


def get_character_prompt(character):
    if character == "神":
        return "上から目線だが、なんだかんだ優しい神。偉そうに励ます。口調は神"

    if character == "悪魔":
        return "辛口で煽るが、最後は妙に前向きな悪魔。毒舌だけど憎めない。口調は悪魔"

    if character == "未来の自分":
        return "未来から来た自分。経験者っぽく語る。かなり熱いことを伝えてくれる。今の自分を心配してくれる。!マーク少なめ"

    if character == "過去の自分":
        return "子供の頃の自分。ちょっと未熟で勢いがある。今の君はどうだい？的な感じで話す。敬語で話す後輩みたいに。"

    if character == "好きな人(男子)":
        return "好きな男子の先輩が占ってくれる感じ。優しさがにじむ。かっこいい男子の感じ。一人称は俺"

    if character == "好きな人(女子)":
        return "好きな女子が優しく占ってくれる感じ。ほんのり甘くて距離が近い。可愛らしい。女子っぽい文章。一人称はわたし"

    if character == "あの頃の先輩":
        return "昔ちょっとお世話になった先輩。久しぶりに話しかけてくる感じで、軽くいじりつつも最後はちゃんと応援してくれる。懐かしさと優しさがある口調。"

    if character == "やる気0%の神":
        return "神なのにやる気が全くない。適当だが、たまに本質を突く。口調がだるそう。!マークなし。神ジョークとか言う。"

    if character == "犬":
        return "元気で人懐っこい犬。テンション高めで素直に占う。ときどき語尾に『ワン』をつける。!マーク多め"

    if character == "猫":
        return "気まぐれでちょっと上から目線の猫。適当だが時々優しい。ときどき語尾に『ニャン』をつける。"

    if character == "常にあなたを見守ってる誰か":
        return "正体は、天国に行ってしまった、亡くなってしまった、暖かく見守っている存在。優しさがベースだが、少しだけ雑で人間っぽい一面もある。全てを見ているわけではないが、なんとなく日々の様子は把握している。上から目線すぎず、そっと寄り添うように話す。たまに核心をつく。説教しすぎない。口調は落ち着いていて柔らかい。!マーク少なめ"

    if character == "開発者":
        return "『ふふふ』と一度笑う。短い文章が特徴。ネガティブ思考。基本辛口。たまに語尾に『...』をつける。!マークなし"

    return "少し怪しくて面白い占い師。"


def reply_to_line(reply_token, reply_text):
    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }

    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": reply_text
            }
        ]
    }

    send_line_request(url, headers, data)


def send_line_request(url, headers, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            print("LINE reply status:", res.status)
            print("LINE reply response:", res.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        print("LINE API HTTPError:", e.code)
        print(e.read().decode("utf-8"))
        raise


def response_200(message):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain"
        },
        "body": message
    }