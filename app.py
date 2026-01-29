from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import TextMessage, Configuration, ApiClient, ReplyMessageRequest
import os
import re
import logging

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

# ------------------------
# LINE Bot configuration
# ------------------------
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
messaging_api = MessagingApi(configuration)

from grammar_checker import EnglishGrammarChecker

# Initialize grammar checker
grammar_checker = EnglishGrammarChecker(api_key=GEMINI_API_KEY)

import threading

@app.route("/callback", methods=['POST'])
def callback():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("[Line Bot] Request body: " + body)

    # 驗證簽名
    try:
        # 驗證通過後，將處理邏輯丟到背景執行緒
        # 注意: 這裡我們不直接呼叫 handler.handle，而是自己解析後處理，或者直接把 handler.handle 丟進去
        # 為了簡單與相容性，我們將 handler.handle 包在執行緒中
        # 但必須確認 signature 是否有效。handler.handle 內部會驗證，但如果丟到背景，主執行緒無法捕獲 InvalidSignatureError
        # 
        # 比較好的做法是：
        # 1. 這裡先做簡單的簽名驗證 (handler 其實沒有獨立的驗證方法，它是在 handle 裡做的)
        # 2. 由於我們無法在此直接驗證，我們選擇直接回 OK，讓背景去跑。
        #    如果簽名錯誤，背景會 log warning，這可以接受。
        
        def run_handler():
            try:
                handler.handle(body, signature)
            except InvalidSignatureError:
                logger.warning("[Line Bot] Invalid signature in background task")
            except Exception as e:
                logger.error(f"[Line Bot] Background processing error: {e}")

        # 啟動背景執行緒
        thread = threading.Thread(target=run_handler)
        thread.start()
        
    except Exception as e:
        logger.error(f"[Line Bot] Callback error: {e}")
        abort(500)

    # 立刻回傳 OK，避免 LINE 重試
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理收到的訊息"""
    # Debug: Check delivery context
    try:
        logger.info(f"[Line Bot] Delivery Context: {event.delivery_context}")
        if event.delivery_context:
            logger.info(f"[Line Bot] Is Redelivery Raw: {event.delivery_context.is_redelivery}")
    except Exception as e:
        logger.error(f"[Line Bot] Error checking delivery context: {e}")

    # 檢查是否為重送 (Redelivery)
    if event.delivery_context and event.delivery_context.is_redelivery:
        logger.warning(f"[Line Bot] Redelivery detected. Skipping processing. Reply Token: {event.reply_token}")
        return

    user_message = event.message.text
    
    logger.info(f"[Line Bot] Received message: {user_message}")
    
    # 進行文法檢查
    correction_result = grammar_checker.check_and_correct_grammar(user_message)
    
    if correction_result == "No corrections needed." or not correction_result:
        logger.info(f"[Line Bot] No corrections needed or empty result: {correction_result}")
        return
    
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
        logger.info("[Line Bot] Sent correction result")
    except Exception as e:
        logger.error(f"[Line Bot] Failed to send message: {e}")

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