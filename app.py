from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import MessagingApi, MessagingApiBlob
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import TextMessage, Configuration, ApiClient, ReplyMessageRequest
import os
import re
import ssl
import logging
import requests
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ------------------------
# Environment variables
# ------------------------
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ------------------------
# LINE Bot configuration
# ------------------------
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
messaging_api = MessagingApi(configuration)

class EnglishGrammarChecker:
    def __init__(self):
        self.english_pattern = re.compile(r'[a-zA-Z]+')
        
    def is_english_text(self, text):
        """Check if the text is mostly English"""
        # 移除標點符號和數字
        clean_text = re.sub(r'[^\w\s]', '', text)
        words = clean_text.split()
        
        if not words:
            return False
            
        english_words = [word for word in words if self.english_pattern.search(word)]
        english_ratio = len(english_words) / len(words)
        
        # 如果英文單詞比例超過70%，認為是英文文本
        return english_ratio > 0.7
    
    def check_and_correct_grammar(self, text):
        """Use Gemini API to check and correct English grammar"""
        prompt = f"""
        You are a helpful English grammar and spelling corrector.
        Check the following sentence and provide corrections if needed.
        If there is no error, reply with 'No corrections needed.'
        If there are mistakes, reply with the corrected sentence and a short explanation.

        Sentence: {text}
        """
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": f"{GEMINI_API_KEY}"
        }
        data = {
            'contents': [{
                'parts': [{
                    'text': prompt
                }]
            }],
            'generationConfig': {
                'temperature': 0.3,  # Controls randomness (0.0 to 2.0 for gemini-1.5-flash)
                'maxOutputTokens': 200  # Limits response length
            }
        }
        try:
            response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            result = response.json()
            # Gemini returns output text under 'candidates' -> [0] -> 'content'
            corrected_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            return corrected_text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "Sorry, the grammar correction service is temporarily unavailable."

# Initialize grammar checker
grammar_checker = EnglishGrammarChecker()

@app.route("/callback", methods=['POST'])
def callback():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 驗證簽名
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理收到的訊息"""
    user_message = event.message.text
    
    logger.info(f"Received message: {user_message}")
    
    # 檢查是否為英文文本
    if not grammar_checker.is_english_text(user_message):
        logger.info("Not English text, skipping")
        return
    
    # 進行文法檢查
    correction_result = grammar_checker.check_and_correct_grammar(user_message)
    
    # 回覆修正結果
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=correction_result)]
                )
            )
        logger.info("Sent correction result")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

@app.route("/health", methods=['GET'])
def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "Line Grammar Bot"}, 200

if __name__ == "__main__":
    # 檢查必要的環境變數
    required_env_vars = [
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_CHANNEL_SECRET',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    logger.info("Line Grammar Bot Starting...")
    app.run(host='0.0.0.0', port=8000, debug=False)