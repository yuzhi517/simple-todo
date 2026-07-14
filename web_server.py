import http.server
import os

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web'))
http.server.HTTPServer(('', 3000), NoCacheHandler).serve_forever()
