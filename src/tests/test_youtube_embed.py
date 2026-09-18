import unittest
from unittest.mock import patch

from qt_api import QApplication
from windows.tools.youtube_embed import service


class YouTubeEmbedServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_suggestions_parse_jsonp_response(self):
        response = (
            b'google.sbox.p50(["jazz",[["jazz music",0],["jazz piano",0]]])'
        )
        with patch.object(service, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = response

            suggestions = service.get_suggestions("jazz")

        self.assertEqual(suggestions, ["jazz music", "jazz piano"])
        request = urlopen.call_args.args[0]
        self.assertIn("client=youtube", request.full_url)
        self.assertIn("ds=yt", request.full_url)
        self.assertIn("q=jazz", request.full_url)

    def test_duration_formatting(self):
        self.assertEqual(service._format_duration(3723), "1:02:03")
        self.assertEqual(service._format_duration(83), "1:23")
        self.assertEqual(service._format_duration(None), "")



if __name__ == "__main__":
    unittest.main()
