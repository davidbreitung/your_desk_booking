"""Local-only UI fixture server; expose only explicit frontend/test files."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

root=Path(__file__).resolve().parent.parent
routes={'/':root/'dev/floorplan.html',
        '/frontend/desk-booking-floorplan.js':root/'custom_components/desk_booking/frontend/desk-booking-floorplan.js',
        '/frontend/model.js':root/'custom_components/desk_booking/frontend/model.js'}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=routes.get(urlsplit(self.path).path)
        if not path:
            self.send_error(404);return
        data=path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type','text/javascript; charset=utf-8' if path.suffix=='.js' else 'text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.end_headers();self.wfile.write(data)
    def log_message(self,*args):pass
HTTPServer(('127.0.0.1',8765),Handler).serve_forever()
