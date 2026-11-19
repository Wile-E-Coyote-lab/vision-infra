from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MockLTXHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        print(f"[*] Mock LTX API received request body: {body}")
        
        # Verify Authorization header exists
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode('utf-8'))
            return

        # Return successful V2 mock response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        mock_response = {
            "id": "job_test_98765",
            "status": "completed",
            "output_url": "http://127.0.0.1:8081/mock_video.mp4"
        }
        self.wfile.write(json.dumps(mock_response).encode('utf-8'))

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 8081), MockLTXHandler)
    print("[*] Mock LTX V2 Server running on http://127.0.0.1:8081")
    server.serve_forever()
