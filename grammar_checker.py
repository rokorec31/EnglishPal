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
        # Initialize the GenAI client with retry disabled (if supported by SDK version,
        # otherwise we assume default behavior or try to configure http_options)
        # Based on search, http_options might be available.
        # But for safety with this specific SDK version (google-genai), let's try standard init 
        # and see if we can pass config.
        # Actually, for google-genai v0.3+, it's often:
        self.client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1beta'}) 
        # Note: 'retry' key in http_options depends on the underlying transport.

    def is_english_text(self, text):
        """Check if the text is mostly English using langdetect"""
        try:
            # Detect language
            lang = detect(text)
            return lang == 'en'
        except Exception as e:
            # Fallback for short text or errors
            logger.warning(f"[Gemini] Language detection failed: {e}")
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
            You are a strict English grammar and spelling corrector.
            Your task is to correct the following sentence.
            
            Rules:
            1. If there are no errors, reply ONLY with: "No corrections needed."
            2. If there are errors, provide ONLY ONE corrected sentence (the most natural/colloquial usage).
            3. Do NOT provide multiple options.
            4. Do NOT use bold text (like **text**) or Markdown formatting. Keep it plain text.
            5. Do NOT be chatty. Do NOT say "Actually..." or "Here are options...".
            6. Format your response exactly like this:
               Corrected: [Your correction here]
               Explanation: [Brief explanation here]

            Sentence: {text}
            """
        else:
            prompt = f"""
            The following text is not in English:
            {text}

            Please translate this into natural, correct English.
            Do NOT use Markdown.
            Format your response exactly like this:
            Translation: [Your English translation here]
            """
        
        try:
            # Call Gemini API using the SDK
            # Using 'gemini-3-flash-preview' as requested
            # To disable retry, we might need to rely on the client config or external library settings if exposed.
            # But here we just proceed with the call.
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
                logger.warning("[Gemini] Returned empty response")
                return ""
                
        except Exception as e:
            logger.error(f"[Gemini] API error: {e}")
            return "Sorry, the grammar correction service is temporarily unavailable."
