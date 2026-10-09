"""Regression checks for interruption-safe full dataset downloads."""
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("fetch_full", Path(__file__).with_name("fetch-full-data.py"))
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


class Response(io.BytesIO):
    def __init__(self, body, total, status=200, start=0, fail_after=None):
        super().__init__(body)
        self.status = status
        self.headers = {"Content-Length": str(total - start)}
        if status == 206:
            self.headers["Content-Range"] = f"bytes {start}-{total - 1}/{total}"
        self.fail_after = fail_after

    def read(self, size=-1):
        if self.fail_after is not None and self.tell() >= self.fail_after:
            raise TimeoutError("simulated network interruption")
        return super().read(size)


class DownloadRegression(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.partial = Path(self.directory.name) / "archive.part"
        self.payload = bytes(range(251)) * 6000
        self.prefix = self.payload[:400000]
        self.partial.write_bytes(self.prefix)

    def receive(self, response):
        fetch.receive_response(response, self.partial, len(self.payload), lambda *args: None)

    def test_ignored_range_compares_prefix_then_appends(self):
        self.receive(Response(self.payload, len(self.payload)))
        self.assertEqual(self.partial.read_bytes(), self.payload)

    def test_early_disconnect_preserves_longer_saved_prefix(self):
        with self.assertRaisesRegex(RuntimeError, "Connection ended early"):
            self.receive(Response(self.payload[:100000], len(self.payload)))
        self.assertEqual(self.partial.read_bytes(), self.prefix)

    def test_timeout_after_append_preserves_new_progress(self):
        with self.assertRaises(TimeoutError):
            self.receive(Response(self.payload, len(self.payload), fail_after=800000))
        retained = self.partial.read_bytes()
        self.assertGreater(len(retained), len(self.prefix))
        self.assertEqual(retained, self.payload[:len(retained)])
        self.receive(Response(self.payload, len(self.payload)))
        self.assertEqual(self.partial.read_bytes(), self.payload)

    def test_supported_range_resumes(self):
        start = len(self.prefix)
        self.receive(Response(self.payload[start:], len(self.payload), 206, start))
        self.assertEqual(self.partial.read_bytes(), self.payload)

    def test_changed_remote_content_is_rejected_without_truncation(self):
        changed = b"X" + self.payload[1:]
        with self.assertRaisesRegex(RuntimeError, "does not match the saved prefix"):
            self.receive(Response(changed, len(self.payload)))
        self.assertEqual(self.partial.read_bytes(), self.prefix)

    def test_incorrect_range_is_rejected_without_writing(self):
        response = Response(self.payload, len(self.payload), 206, 0)
        with self.assertRaisesRegex(RuntimeError, "Incorrect HTTP range"):
            self.receive(response)
        self.assertEqual(self.partial.read_bytes(), self.prefix)


if __name__ == "__main__":
    unittest.main()
