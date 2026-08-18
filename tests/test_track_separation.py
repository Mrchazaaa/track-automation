import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import TrackSeparation


class Response:
    def __init__(self, status_code=200, payload=None, text="response", chunks=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self._chunks = chunks or []

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def iter_content(self, chunk_size):
        return iter(self._chunks)


class LalalAITests(unittest.TestCase):
    def setUp(self):
        self.client = TrackSeparation.LalalAI("test-key")

    @patch("TrackSeparation.requests.get")
    def test_check_limits_returns_successful_response(self, mock_get):
        payload = {"status": "success", "process_duration_left": 12.5}
        mock_get.return_value = Response(payload=payload)

        self.assertEqual(self.client.check_limits(), payload)
        mock_get.assert_called_once_with(
            "https://www.lalal.ai/billing/get-limits/", params={"key": "test-key"}
        )

    @patch("TrackSeparation.requests.post")
    def test_split_audio_sends_expected_payload(self, mock_post):
        mock_post.return_value = Response(payload={"status": "success", "id": "job-1"})

        result = self.client.split_audio("file-1", "drum")

        self.assertEqual(result["id"], "job-1")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"], {"Authorization": "license test-key"})
        self.assertEqual(
            json.loads(kwargs["data"]["params"]),
            [{"id": "file-1", "stem": "drum", "enhanced_processing_enabled": True}],
        )

    @patch("TrackSeparation.requests.get")
    def test_download_file_writes_nonempty_chunks(self, mock_get):
        mock_get.return_value = Response(chunks=[b"first", b"", b"second"])
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "track.mp3"

            self.assertTrue(self.client.download_file("https://example.test/track", output))
            self.assertEqual(output.read_bytes(), b"firstsecond")

        mock_get.assert_called_once_with("https://example.test/track", stream=True)

    @patch("TrackSeparation.time.sleep")
    def test_wait_for_completion_returns_split_when_task_succeeds(self, mock_sleep):
        self.client.check_status = Mock(
            side_effect=[
                {"status": "success", "result": {"file-1": {"status": "success", "task": {"state": "progress", "progress": 50}}}},
                {"status": "success", "result": {"file-1": {"status": "success", "task": {"state": "success"}, "split": {"stem_track": "stem-url"}}}},
            ]
        )

        result = self.client.wait_for_completion("file-1", timeout=1)

        self.assertEqual(result, {"stem_track": "stem-url"})
        self.assertEqual(self.client.check_status.call_count, 2)
        mock_sleep.assert_called_once_with(10)


class SplitInstructionTests(unittest.TestCase):
    @patch("TrackSeparation.LalalAI")
    def test_split_instr_downloads_stem_and_backing_track(self, mock_client_class):
        client = mock_client_class.return_value
        client.check_limits.return_value = {"status": "success"}
        client.upload_file.return_value = {"id": "upload-1"}
        client.wait_for_completion.return_value = {
            "stem": "drum",
            "stem_track": "https://example.test/drums",
            "back_track": "https://example.test/backing",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "song.mp3"
            input_file.write_bytes(b"audio")
            output_dir = Path(temp_dir) / "output"

            result = TrackSeparation.split_instr(
                input_file, "api-key", output_dir, "drum", "song_no_drums"
            )

            self.assertEqual(result["stem_track"], output_dir / "song_drum.mp3")
            self.assertEqual(result["back_track"], output_dir / "song_no_drums.mp3")
            self.assertEqual(
                client.download_file.call_args_list,
                [
                    unittest.mock.call("https://example.test/drums", str(output_dir / "song_drum.mp3")),
                    unittest.mock.call("https://example.test/backing", str(output_dir / "song_no_drums.mp3")),
                ],
            )


if __name__ == "__main__":
    unittest.main()
