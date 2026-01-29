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
        self.api_url = "http://test.url"
        self.checker = EnglishGrammarChecker(self.api_key, self.api_url)

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

    @patch('requests.post')
    def test_correction_english(self, mock_post):
        # Mock successful API response for correction
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Corrected text'}]}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Mock is_english_text to avoid complex logic and ensure path
        with patch.object(self.checker, 'is_english_text', return_value=True):
            result = self.checker.check_and_correct_grammar("Test text")
        
        self.assertEqual(result, "Corrected text")
        
        # Verify API was called with correct URL and headers
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], self.api_url)
        self.assertEqual(kwargs['headers']['X-goog-api-key'], self.api_key)
        
        # Verify prompt contained instruction for checking
        sent_data = json.loads(kwargs['data'])
        prompt_text = sent_data['contents'][0]['parts'][0]['text']
        self.assertIn("grammar and spelling corrector", prompt_text)

    @patch('requests.post')
    def test_translation_non_english(self, mock_post):
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Translated text'}]}}]
        }
        mock_post.return_value = mock_response

        # Mock is_english_text to return False
        with patch.object(self.checker, 'is_english_text', return_value=False):
            result = self.checker.check_and_correct_grammar("Non-english text")
            
        self.assertEqual(result, "Translated text")
        
        # Verify prompt contained instruction for translation
        args, kwargs = mock_post.call_args
        sent_data = json.loads(kwargs['data'])
        prompt_text = sent_data['contents'][0]['parts'][0]['text']
        self.assertIn("not in English", prompt_text)

    @patch('requests.post')
    def test_api_error(self, mock_post):
        # Mock request exception
        mock_post.side_effect = Exception("API connection error")
        
        with patch.object(self.checker, 'is_english_text', return_value=True):
            result = self.checker.check_and_correct_grammar("Test")
            
        self.assertEqual(result, "Sorry, the grammar correction service is temporarily unavailable.")

if __name__ == '__main__':
    unittest.main()
