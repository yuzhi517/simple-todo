import json
import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock
from urllib.request import urlopen

import run


class HealthHandler(BaseHTTPRequestHandler):
    api_status = "ok"
    delay = 0

    def do_GET(self):
        if self.delay:
            time.sleep(self.delay)
        if self.path == "/health":
            payload = json.dumps({"status": self.api_status}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

    def log_message(self, format, *args):
        pass


class LauncherTests(unittest.TestCase):
    def test_reserve_socket_uses_available_dynamic_port(self):
        occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupied.bind((run.HOST, 0))
        occupied.listen()
        occupied_port = occupied.getsockname()[1]
        try:
            reserved = run.reserve_socket()
            self.assertNotEqual(reserved.getsockname()[1], occupied_port)
            reserved.close()
        finally:
            occupied.close()

    def test_wait_for_health_accepts_ready_services(self):
        api = HTTPServer((run.HOST, 0), HealthHandler)
        web = HTTPServer((run.HOST, 0), HealthHandler)
        threads = [
            threading.Thread(target=api.serve_forever, daemon=True),
            threading.Thread(target=web.serve_forever, daemon=True),
        ]
        for thread in threads:
            thread.start()
        try:
            run.wait_for_health(
                f"http://{run.HOST}:{api.server_address[1]}",
                f"http://{run.HOST}:{web.server_address[1]}",
                run.FailureState(),
                timeout=2,
            )
        finally:
            api.shutdown()
            web.shutdown()
            api.server_close()
            web.server_close()

    def test_wait_for_health_reports_thread_failure(self):
        failed = run.FailureState()
        failed.set("backend", RuntimeError("boom"))
        with self.assertRaisesRegex(RuntimeError, "backend.*boom"):
            run.wait_for_health(
                "http://127.0.0.1:1",
                "http://127.0.0.1:2",
                failed,
                timeout=0.1,
            )

    def test_wait_for_health_times_out(self):
        with self.assertRaises(TimeoutError):
            run.wait_for_health(
                "http://127.0.0.1:1",
                "http://127.0.0.1:2",
                run.FailureState(),
                timeout=0.2,
            )

    def test_in_process_services_start_and_cleanup_twice(self):
        logger = run.configure_logging()
        services = run.InProcessServices(run.os.path.dirname(run.__file__), logger)
        services.start()
        try:
            services.wait_until_ready(timeout=5)
            with urlopen(f"{services.api_url}/health", timeout=1) as response:
                self.assertEqual(response.status, 200)
            self.assertIn(f"apiPort={services.api_port}", services.browser_url)
        finally:
            services.cleanup()
            services.cleanup()

    def test_smoke_test_does_not_open_browser_or_notifier(self):
        with mock.patch.object(run.webbrowser, "open") as open_browser, \
                mock.patch.object(run.InProcessServices, "start_notifier") as notifier:
            result = run.run_in_process(
                run.os.path.dirname(run.__file__), True, run.configure_logging()
            )
        self.assertEqual(result, 0)
        open_browser.assert_not_called()
        notifier.assert_not_called()


if __name__ == "__main__":
    unittest.main()
