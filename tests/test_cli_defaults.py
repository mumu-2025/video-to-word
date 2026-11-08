import inspect
import unittest

from video_to_word import __version__
from video_to_word.cli import build_parser, main
from video_to_word import download, pipeline


class TestDefaults(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.1.1")

    def test_pipeline_prefer_subs_default_false(self):
        sig = inspect.signature(pipeline.run_pipeline)
        self.assertIs(sig.parameters["prefer_subs"].default, False)

    def test_download_prefer_subs_default_false(self):
        sig = inspect.signature(download.download_url)
        self.assertIs(sig.parameters["prefer_subs"].default, False)

    def test_cli_prefer_subs_opt_in(self):
        parser = build_parser()
        args = parser.parse_args(["--url", "https://example.com/x"])
        self.assertFalse(args.prefer_subs)
        self.assertFalse(args.no_subs)
        args2 = parser.parse_args(["--url", "https://example.com/x", "--prefer-subs"])
        self.assertTrue(args2.prefer_subs)
        args3 = parser.parse_args(["--url", "https://example.com/x", "--use-subs"])
        self.assertTrue(args3.prefer_subs)


if __name__ == "__main__":
    unittest.main()
