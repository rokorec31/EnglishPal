import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from grammar_checker import EnglishGrammarChecker
import json

class TestEnglishGrammarChecker(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_key"
        # Patch the Client class where it is imported in grammar_checker
        self.client_patcher = patch('grammar_checker.genai.Client')
        self.mock_client_cls = self.client_patcher.start()
        self.mock_client_instance = self.mock_client_cls.return_value
        
        self.checker = EnglishGrammarChecker(self.api_key)

    def tearDown(self):
        self.client_patcher.stop()

    @patch('grammar_checker.detect')
    def test_is_english_text_detected(self, mock_detect):
        # Test case: langdetect returns 'en'
        mock_detect.return_value = 'en'
        self.assertTrue(self.checker.is_english_text("Hello world"))
        
    @patch('grammar_checker.detect')
    def test_is_non_english_text_detected(self, mock_detect):
        # Test case: langdetect returns 'zh-cn'
        mock_detect.return_value = 'zh-cn'
        self.assertFalse(self.checker.is_english_text("你好"))

    def test_is_english_text_fallback(self):
        # Force fallback by mocking detect to raise exception
        with patch('grammar_checker.detect', side_effect=Exception("Error")):
            # Uses regex. "Hello world" is 100% english
            self.assertTrue(self.checker.is_english_text("Hello world"))
            # "你好" is 0% english
            self.assertFalse(self.checker.is_english_text("你好"))

    def test_correction_english(self):
        # Mock successful API response for correction
        mock_response = MagicMock()
        mock_response.text = "Corrected text"
        self.mock_client_instance.models.generate_content.return_value = mock_response

        # Mock is_english_text to avoid complex logic and ensure path
        with patch.object(self.checker, 'is_english_text', return_value=True):
            result = self.checker.check_and_correct_grammar("Test text")
        
        self.assertEqual(result, "Corrected text")
        
        # Verify API was called with correct model and config
        self.mock_client_instance.models.generate_content.assert_called_once()
        args, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertEqual(kwargs['model'], 'gemini-3-flash-preview')
        self.assertIn("grammar and spelling corrector", kwargs['contents'])

    def test_translation_non_english(self):
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "Translated text"
        self.mock_client_instance.models.generate_content.return_value = mock_response

        # Mock is_english_text to return False
        with patch.object(self.checker, 'is_english_text', return_value=False):
            result = self.checker.check_and_correct_grammar("Non-english text")
            
        self.assertEqual(result, "Translated text")
        
        # Verify prompt contained instruction for translation
        args, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertIn("not in English", kwargs['contents'])

    def test_api_error(self):
        # Mock request exception
        self.mock_client_instance.models.generate_content.side_effect = Exception("API connection error")
        
        with patch.object(self.checker, 'is_english_text', return_value=True):
            result = self.checker.check_and_correct_grammar("Test")
            
        self.assertEqual(result, "Sorry, the grammar correction service is temporarily unavailable.")

if __name__ == '__main__':
    unittest.main()
