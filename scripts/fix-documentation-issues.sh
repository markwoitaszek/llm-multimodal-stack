#!/bin/bash

# Phase 3 Documentation Issues - Quick Fix Script
# This script addresses immediate documentation issues while Phase 3 is being planned

set -e

echo "🔧 Phase 3 Documentation Issues - Quick Fix Script"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "📋 Current Issues Identified:"
echo "  - Markdown files being downloaded instead of rendered"
echo "  - Broken internal links in documentation"
echo "  - Missing MIME types for .md files"
echo "  - Navigation issues between documentation pages"
echo ""

# Create backup of current nginx configuration
echo "💾 Creating backup of current nginx configuration..."
cp services/ai-agents/web/nginx.conf services/ai-agents/web/nginx.conf.backup
echo "✅ Backup created: services/ai-agents/web/nginx.conf.backup"

# Update nginx configuration to handle markdown files better
echo "🔧 Updating nginx configuration for better markdown handling..."

cat > services/ai-agents/web/nginx.conf << 'EOF'
user appuser;
worker_processes auto;
pid /tmp/nginx/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Add markdown MIME type
    types {
        text/markdown md;
        text/html html htm;
        application/x-yaml yaml yml;
        application/json json;
    }

    sendfile on;
    keepalive_timeout 65;

    server {
        listen 3000;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html index.htm;

        # Handle React Router
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API proxy
        location /api/ {
            proxy_pass http://ai-agents:8003/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Documentation routes with better markdown handling
        location /docs/ {
            alias /usr/share/nginx/html/docs/;
            try_files $uri $uri/ /docs/index.html;
            
            # Set proper MIME types
            location ~* \.(yaml|yml)$ {
                add_header Content-Type application/x-yaml;
            }
            location ~* \.(json)$ {
                add_header Content-Type application/json;
            }
            location ~* \.(md)$ {
                add_header Content-Type text/markdown;
                add_header Content-Disposition "inline";
            }
        }

        # API Documentation (Swagger UI)
        location /api-docs/ {
            alias /usr/share/nginx/html/docs/;
            try_files $uri $uri/ /docs/swagger-ui.html;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

echo "✅ Updated nginx configuration with better markdown handling"

# Create a simple markdown-to-HTML converter script
echo "📝 Creating markdown-to-HTML converter script..."

mkdir -p scripts/documentation

cat > scripts/documentation/convert-markdown.sh << 'EOF'
#!/bin/bash

# Simple markdown to HTML converter for documentation
# This is a temporary solution until Phase 3 implementation

INPUT_FILE="$1"
OUTPUT_FILE="$2"

if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <input.md> <output.html>"
    exit 1
fi

# Create basic HTML wrapper
cat > "$OUTPUT_FILE" << 'HTML_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation - Multimodal LLM Stack</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1, h2, h3 { color: #2c3e50; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
        blockquote { border-left: 4px solid #ddd; margin: 0; padding-left: 20px; color: #666; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .nav { background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
        .nav a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/docs/">📚 Documentation Home</a>
        <a href="/api-docs/">🔧 API Documentation</a>
        <a href="/">🏠 Main Interface</a>
    </div>
HTML_EOF

# Convert markdown to HTML (basic conversion)
if command -v pandoc &> /dev/null; then
    pandoc "$INPUT_FILE" >> "$OUTPUT_FILE"
else
    echo "<h1>Markdown File: $(basename "$INPUT_FILE")</h1>" >> "$OUTPUT_FILE"
    echo "<p><strong>Note:</strong> Install pandoc for proper markdown rendering.</p>" >> "$OUTPUT_FILE"
    echo "<pre>" >> "$OUTPUT_FILE"
    cat "$INPUT_FILE" >> "$OUTPUT_FILE"
    echo "</pre>" >> "$OUTPUT_FILE"
fi

# Close HTML
echo "</body></html>" >> "$OUTPUT_FILE"

echo "✅ Converted $INPUT_FILE to $OUTPUT_FILE"
EOF

chmod +x scripts/documentation/convert-markdown.sh
echo "✅ Created markdown converter script"

# Create documentation index with working links
echo "📋 Creating documentation index with working links..."

cat > docs/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation - Multimodal LLM Stack</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
        .nav { background: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 30px; text-align: center; }
        .nav a { margin: 0 15px; text-decoration: none; color: #007bff; font-weight: 600; }
        .nav a:hover { text-decoration: underline; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }
        .doc-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .doc-item { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
        .doc-item h3 { margin-top: 0; color: #2c3e50; }
        .doc-item p { color: #6c757d; margin-bottom: 15px; }
        .doc-item a { color: #007bff; text-decoration: none; font-weight: 600; }
        .doc-item a:hover { text-decoration: underline; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }
        .status.working { background: #d4edda; color: #155724; }
        .status.issue { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Multimodal LLM Stack Documentation</h1>
        
        <div class="nav">
            <a href="/">🏠 Main Interface</a>
            <a href="/api-docs/">🔧 API Documentation</a>
            <a href="/docs/search.html">🔍 Search</a>
            <a href="/docs/playground.html">🎮 Playground</a>
        </div>

        <div class="section">
            <h2>🚀 Getting Started</h2>
            <div class="doc-grid">
                <div class="doc-item">
                    <h3>Quick Start Guide</h3>
                    <p>Get up and running with the Multimodal LLM Stack in minutes.</p>
                    <a href="/docs/quick-start.md">Read Guide</a>
                    <span class="status issue">Needs HTML conversion</span>
                </div>
                <div class="doc-item">
                    <h3>Configuration</h3>
                    <p>Learn how to configure the stack for your environment.</p>
                    <a href="/docs/configuration.md">Read Guide</a>
                    <span class="status issue">Needs HTML conversion</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔧 API Documentation</h2>
            <div class="doc-grid">
                <div class="doc-item">
                    <h3>Interactive API Docs</h3>
                    <p>Explore APIs with Swagger UI interface.</p>
                    <a href="/api-docs/">Open Swagger UI</a>
                    <span class="status working">Working</span>
                </div>
                <div class="doc-item">
                    <h3>API Reference</h3>
                    <p>Complete API documentation with examples.</p>
                    <a href="/docs/api-reference.md">Read Reference</a>
                    <span class="status issue">Needs HTML conversion</span>
                </div>
                <div class="doc-item">
                    <h3>OpenAPI Specifications</h3>
                    <p>Machine-readable API specifications.</p>
                    <a href="/docs/openapi/combined.yaml">View Specs</a>
                    <span class="status working">Working</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🛠️ Development & Deployment</h2>
            <div class="doc-grid">
                <div class="doc-item">
                    <h3>Development Guide</h3>
                    <p>Set up development environment and contribute.</p>
                    <a href="/docs/development.md">Read Guide</a>
                    <span class="status issue">Needs HTML conversion</span>
                </div>
                <div class="doc-item">
                    <h3>Deployment Guide</h3>
                    <p>Deploy the stack to production environments.</p>
                    <a href="/docs/development-deployment.md">Read Guide</a>
                    <span class="status issue">Needs HTML conversion</span>
                </div>
                <div class="doc-item">
                    <h3>Troubleshooting</h3>
                    <p>Common issues and their solutions.</p>
                    <a href="/docs/troubleshooting.md">Read Guide</a>
                    <span class="status issue">Needs HTML conversion</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📋 Phase 3 Status</h2>
            <div class="doc-item">
                <h3>Documentation Issues Identified</h3>
                <p>Several issues have been identified that will be addressed in Phase 3:</p>
                <ul>
                    <li>Markdown files need HTML conversion</li>
                    <li>Internal links need fixing</li>
                    <li>Navigation system needs improvement</li>
                    <li>Search functionality needs enhancement</li>
                </ul>
                <a href="/docs/PHASE_3_DOCUMENTATION_REVIEW_ISSUE.md">View Phase 3 Plan</a>
                <span class="status issue">In Planning</span>
            </div>
        </div>
    </div>
</body>
</html>
EOF

echo "✅ Created documentation index with working links"

# Rebuild and restart the service
echo "🔄 Rebuilding and restarting AI Agents Web Interface..."
docker-compose build ai-agents-web
docker-compose up ai-agents-web -d

echo ""
echo "✅ Quick fixes applied!"
echo ""
echo "📋 What was fixed:"
echo "  - Added proper MIME types for .md files"
echo "  - Created markdown-to-HTML converter script"
echo "  - Created documentation index with working links"
echo "  - Updated nginx configuration"
echo ""
echo "🌐 Access points:"
echo "  - Main Interface: http://localhost:3001"
echo "  - Documentation: http://localhost:3001/docs/"
echo "  - API Documentation: http://localhost:3001/api-docs/"
echo ""
echo "⚠️  Note: This is a temporary fix. Phase 3 will provide a complete solution."
echo ""
echo "📝 Next steps:"
echo "  1. Create GitHub issue for Phase 3"
echo "  2. Implement proper markdown-to-HTML pipeline"
echo "  3. Fix all internal links"
echo "  4. Enhance search functionality"
echo ""
echo "🎯 Phase 3 issue created in: docs/PHASE_3_DOCUMENTATION_REVIEW_ISSUE.md"
