import unittest
from video_to_word.util import clean_paragraphs, safe_filename


class TestUtil(unittest.TestCase):
    def test_safe_filename(self):
        name = safe_filename('a/b:c*d?')
        self.assertNotIn('/', name)
        self.assertNotIn(':', name)
        self.assertNotIn('*', name)
        self.assertNotIn('?', name)
        self.assertIn('hello', safe_filename('hello/world'))
        self.assertTrue(len(safe_filename('x' * 200)) <= 80)

    def test_clean_paragraphs_zh(self):
        text = "今天天气很好。我们去公园散步。\n\n第二段内容在这里！"
        paras = clean_paragraphs(text)
        self.assertTrue(len(paras) >= 1)
        self.assertTrue(any('公园' in p for p in paras))

    def test_clean_empty(self):
        self.assertEqual(clean_paragraphs(''), [])


if __name__ == '__main__':
    unittest.main()
