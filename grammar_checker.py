from langdetect import detect
import re
import requests
import json
import logging

logger = logging.getLogger(__name__)

class EnglishGrammarChecker:
    def __init__(self, api_key, api_url):
        self.english_pattern = re.compile(r'[a-zA-Z]+')
        self.api_key = api_key
        self.api_url = api_url
        
    def is_english_text(self, text):
        """Check if the text is mostly English using langdetect"""
        try:
            # Detect language
            lang = detect(text)
            return lang == 'en'
        except Exception as e:
            # Fallback for short text or errors
            logger.warning(f"Language detection failed: {e}")
            # Fallback to simple regex if detection fails
            clean_text = re.sub(r'[^\w\s]', '', text)
            words = clean_text.split()
            if not words:
                return False
            english_words = [word for word in words if self.english_pattern.search(word)]
            if len(words) == 0: return False
            return (len(english_words) / len(words)) > 0.7
    
    def check_and_correct_grammar(self, text):
        """Check grammar if English, otherwise suggest English translation"""
        if self.is_english_text(text):
            prompt = f"""
            You are a helpful English grammar and spelling corrector.
            Check the following sentence and provide corrections if needed.
            If there is no error, reply with 'No corrections needed.'
            If there are mistakes, reply with the corrected sentence and a short explanation.

            Sentence: {text}
            """
        else:
            prompt = f"""
            The following text is not in English:
            {text}

            Please provide a natural and correct English version of this sentence.
            """
        
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": f"{self.api_key}"
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
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            result = response.json()
            # Gemini returns output text under 'candidates' -> [0] -> 'content'
            corrected_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            return corrected_text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "Sorry, the grammar correction service is temporarily unavailable."
