#!/usr/bin/env python3
"""
Simple HTTP server to serve the API documentation
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Configuration
PORT = 8080
HOST = "0.0.0.0"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve OpenAPI specs with proper CORS headers"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def guess_type(self, path):
        """Override to set correct MIME types for OpenAPI specs"""
        mimetype, encoding = super().guess_type(path)
        
        if path.endswith('.yaml') or path.endswith('.yml'):
            return 'application/x-yaml'
        elif path.endswith('.json'):
            return 'application/json'
        
        return mimetype

def main():
    """Start the documentation server"""
    # Change to the docs directory
    docs_dir = Path(__file__).parent
    os.chdir(docs_dir)
    
    print(f"🚀 Starting Multimodal LLM Stack API Documentation Server")
    print(f"📁 Serving from: {docs_dir}")
    print(f"🌐 Server running at: http://{HOST}:{PORT}")
    print(f"📚 OpenAPI specs available at:")
    print(f"   - Combined: http://{HOST}:{PORT}/openapi/combined.yaml")
    print(f"   - LiteLLM Router: http://{HOST}:{PORT}/openapi/litellm-router.yaml")
    print(f"   - Multimodal Worker: http://{HOST}:{PORT}/openapi/multimodal-worker.yaml")
    print(f"   - Retrieval Proxy: http://{HOST}:{PORT}/openapi/retrieval-proxy.yaml")
    print(f"   - AI Agents: http://{HOST}:{PORT}/openapi/ai-agents.yaml")
    print(f"🎨 Interactive Swagger UI: http://{HOST}:{PORT}/swagger-ui.html")
    print(f"\n💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {PORT} is already in use")
            print(f"💡 Try a different port or stop the existing server")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()