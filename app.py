from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os
from openai import OpenAI
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set seed for consistent language detection
DetectorFactory.seed = 0

app = Flask(__name__)

# Load environment variables
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()

    # Detect language
    try:
        lang = detect(text)
    except LangDetectException:
        lang = None

    # Generate response based on language
    if lang == 'en':
        # Use ChatGPT to check and correct
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful English grammar and spelling corrector. If the sentence has no errors, replay with 'No corrections needed.' Otherwise, provide only the corrected sentence followed by a short explaintion."},
                {"role": "user", "content": f"Correct this: {text}"}
            ],
            max_tokens=150,
            temperature=0.5
        )
        correction = response.choices[0].message.content.strip()

        if correction != "No corrections needed.":
            # Reply with correction
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=correction)]
                    )
                )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)