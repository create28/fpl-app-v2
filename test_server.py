#!/usr/bin/env python3
"""
Minimal Test Server for Render
==============================

This is a simple HTTP server to test if basic Python HTTP functionality works on Render.
"""

import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        print(f"Received request: {self.path}")
        
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        if self.path == '/':
            # Root endpoint
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>FPL Test Server</title></head>
            <body>
                <h1>FPL Test Server is Running! 🚀</h1>
                <p>Server is working on Render!</p>
                <ul>
                    <li><a href="/health">Health Check</a></li>
                    <li><a href="/test">Test Endpoint</a></li>
                    <li><a href="/api/test">API Test</a></li>
                </ul>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/health':
            # Health check
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'healthy',
                'service': 'FPL Test Server',
                'timestamp': str(datetime.now()),
                'message': 'Server is running on Render!'
            }
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
            
        elif self.path == '/test':
            # Simple test endpoint
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            
            self.wfile.write(b'Test endpoint working! Server is alive.')
            
        elif self.path == '/api/test':
            # API test endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'message': 'API endpoint working!',
                'timestamp': str(datetime.now()),
                'status': 'success'
            }
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
            
        else:
            # 404 for unknown paths
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom logging to see requests in Render logs."""
        print(f"[{datetime.now()}] {format % args}")

def main():
    """Start the test server."""
    port = int(os.getenv('PORT', 8000))
    
    print(f"Starting FPL Test Server on port {port}")
    print("=" * 50)
    print("This is a minimal test server to debug Render deployment")
    print("=" * 50)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, TestHandler)
    
    print(f"Server started successfully on port {port}")
    print(f"Test URLs:")
    print(f"  - Root: http://localhost:{port}/")
    print(f"  - Health: http://localhost:{port}/health")
    print(f"  - Test: http://localhost:{port}/test")
    print(f"  - API: http://localhost:{port}/api/test")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    main()
