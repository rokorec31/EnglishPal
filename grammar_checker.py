from langdetect import detect
import re
from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)

class EnglishGrammarChecker:
    def __init__(self, api_key):
        self.english_pattern = re.compile(r'[a-zA-Z]+')
        self.api_key = api_key
        # Initialize the GenAI client
        self.client = genai.Client(api_key=self.api_key)
        
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
        
        try:
            # Call Gemini API using the SDK
            # Using 'gemini-3-flash-preview' as requested for stability
            response = self.client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_level="low"
                    )
                )
            )
            
            if response.text:
                return response.text.strip()
            else:
                logger.warning("Gemini returned empty response")
                return "" # Return empty string instead of fallback message if actually empty, to let app decide? 
                          # Actually sticking to old behavior of returning strings, but let's be safe.
                          # If text is empty, it usually means blocked content or error.
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "Sorry, the grammar correction service is temporarily unavailable."
