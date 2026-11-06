import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bilibili_downloader.cli import main, parse_video
from yt_dlp.utils import DownloadError


class VideoInputTests(unittest.TestCase):
    def test_bv_preserves_case_of_identifier(self):
        self.assertEqual(parse_video("  bv1xx411c7mD  "), ("BV1xx411c7mD", None))

    def test_url_retains_page(self):
        self.assertEqual(
            parse_video("https://www.bilibili.com/video/BV1xx411c7mD/?p=2&share_source=copy"),
            ("BV1xx411c7mD", 2),
        )

    def test_rejects_invalid_inputs(self):
        for value in ("", "BV123", "BV1xx411c7mDextra", "av123",
                      "https://evil.example/video/BV1xx411c7mD",
                      "https://www.bilibili.com.evil.example/video/BV1xx411c7mD",
                      "https://www.bilibili.com/video/BV1xx411c7mD?p=0",
                      "https://www.bilibili.com/video/BV1xx411c7mD?p=abc",
                      "https://www.bilibili.com/video/BV1xx411c7mD?p=",
                      "https://www.bilibili.com/video/BV1xx411c7mD?p=1&p=2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_video(value)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "videos"
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.enterContext(contextlib.redirect_stdout(self.stdout))
        self.enterContext(contextlib.redirect_stderr(self.stderr))
        self.ffmpeg = self.enterContext(patch("bilibili_downloader.cli.find_ffmpeg", return_value="ffmpeg"))
        self.factory = self.enterContext(patch("bilibili_downloader.cli.YoutubeDL"))
        self.downloader = self.factory.return_value.__enter__.return_value
        self.downloader.extract_info.return_value = {"title": "测试", "formats": []}

    def run_cli(self, *args):
        return main([*args, "-o", str(self.output)])

    def test_default_downloads_first_page_and_prints_directory(self):
        self.assertEqual(self.run_cli("BV1xx411c7mD"), 0)
        self.downloader.extract_info.assert_called_once_with(
            "https://www.bilibili.com/video/BV1xx411c7mD/?p=1", download=True,
        )
        self.assertTrue(self.output.is_dir())
        self.assertIn(str(self.output / "BV1xx411c7mD"), self.stdout.getvalue())

    def test_explicit_page_overrides_url_page(self):
        self.assertEqual(self.run_cli("https://www.bilibili.com/video/BV1xx411c7mD?p=2", "--page", "3"), 0)
        self.assertTrue(self.downloader.extract_info.call_args.args[0].endswith("?p=3"))

    def test_all_parts_clears_url_page(self):
        self.assertEqual(self.run_cli("https://www.bilibili.com/video/BV1xx411c7mD?p=2", "--all-parts"), 0)
        self.assertEqual(self.downloader.extract_info.call_args.args[0], "https://www.bilibili.com/video/BV1xx411c7mD/")
        self.assertFalse(self.factory.call_args.args[0]["noplaylist"])

    def test_info_needs_no_ffmpeg_and_creates_no_output(self):
        self.ffmpeg.return_value = None
        self.assertEqual(self.run_cli("BV1xx411c7mD", "--info"), 0)
        self.assertFalse(self.downloader.extract_info.call_args.kwargs["download"])
        self.assertFalse(self.output.exists())
        self.assertIn("测试", self.stdout.getvalue())

    def test_missing_ffmpeg_fails_before_network(self):
        self.ffmpeg.return_value = None
        self.assertEqual(self.run_cli("BV1xx411c7mD"), 1)
        self.factory.assert_not_called()

    def test_missing_cookie_fails_before_network(self):
        self.assertEqual(self.run_cli("BV1xx411c7mD", "--cookies", str(self.output / "missing.txt")), 1)
        self.factory.assert_not_called()

    def test_failed_download_is_not_reported_as_success(self):
        self.downloader.extract_info.side_effect = DownloadError("HTTP Error 412")
        self.assertEqual(self.run_cli("BV1xx411c7mD"), 1)
        self.assertNotIn("下载完成", self.stdout.getvalue())
        self.assertIn("412", self.stderr.getvalue())

    def test_interactive_input(self):
        with patch("builtins.input", return_value="BV1xx411c7mD"):
            self.assertEqual(self.run_cli(), 0)

    def test_interruption_returns_130(self):
        self.downloader.extract_info.side_effect = KeyboardInterrupt
        self.assertEqual(self.run_cli("BV1xx411c7mD"), 130)


if __name__ == "__main__":
    unittest.main()
