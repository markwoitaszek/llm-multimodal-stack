#!/bin/bash
set -e

# GitHub Wiki Setup Script for Multimodal LLM Stack
echo "📚 Setting up GitHub Wiki documentation..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from the project root."
    exit 1
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed. Please install it first:"
    echo "   https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub. Please run: gh auth login"
    exit 1
fi

# Get repository information
REPO_URL=$(git remote get-url origin)
REPO_NAME=$(basename "$REPO_URL" .git)

echo "📋 Repository: $REPO_NAME"
echo "🔗 Wiki will be available at: https://github.com/$(gh api user --jq .login)/$REPO_NAME/wiki"

# Enable wiki for the repository
echo "🔧 Enabling GitHub Wiki..."
gh api repos/$(gh api user --jq .login)/$REPO_NAME -X PATCH -f has_wiki=true

# Wait a moment for the wiki to be enabled
sleep 2

# Create wiki pages
echo "📝 Creating wiki pages..."

# Create Home page
echo "Creating Home.md..."
gh wiki create "$REPO_NAME" "Home" -b "$(cat docs/wiki/Home.md)"

# Create Getting Started Guide
echo "Creating Getting-Started-Guide.md..."
gh wiki create "$REPO_NAME" "Getting-Started-Guide" -b "$(cat docs/wiki/Getting-Started-Guide.md)"

# Create Setup Wizard Tutorial
echo "Creating Setup-Wizard-Tutorial.md..."
gh wiki create "$REPO_NAME" "Setup-Wizard-Tutorial" -b "$(cat docs/wiki/Setup-Wizard-Tutorial.md)"

# Create additional wiki pages from existing docs
echo "📄 Adding existing documentation to wiki..."

# Add configuration guide
if [ -f "docs/configuration.md" ]; then
    echo "Adding Configuration-Guide.md..."
    gh wiki create "$REPO_NAME" "Configuration-Guide" -b "$(cat docs/configuration.md)"
fi

# Add API reference
if [ -f "docs/api-reference.md" ]; then
    echo "Adding API-Reference.md..."
    gh wiki create "$REPO_NAME" "API-Reference" -b "$(cat docs/api-reference.md)"
fi

# Add development guide
if [ -f "docs/development.md" ]; then
    echo "Adding Development-Guide.md..."
    gh wiki create "$REPO_NAME" "Development-Guide" -b "$(cat docs/development.md)"
fi

# Add troubleshooting guide
if [ -f "docs/troubleshooting.md" ]; then
    echo "Adding Troubleshooting-Guide.md..."
    gh wiki create "$REPO_NAME" "Troubleshooting-Guide" -b "$(cat docs/troubleshooting.md)"
fi

# Add quick start guide
if [ -f "docs/quick-start.md" ]; then
    echo "Adding Quick-Start-Guide.md..."
    gh wiki create "$REPO_NAME" "Quick-Start-Guide" -b "$(cat docs/quick-start.md)"
fi

echo ""
echo "🎉 GitHub Wiki setup completed successfully!"
echo ""
echo "📚 Your wiki is now available at:"
echo "   https://github.com/$(gh api user --jq .login)/$REPO_NAME/wiki"
echo ""
echo "📋 Created pages:"
echo "   - Home (main landing page)"
echo "   - Getting-Started-Guide"
echo "   - Setup-Wizard-Tutorial"
echo "   - Configuration-Guide"
echo "   - API-Reference"
echo "   - Development-Guide"
echo "   - Troubleshooting-Guide"
echo "   - Quick-Start-Guide"
echo ""
echo "🔧 To update wiki pages in the future:"
echo "   1. Edit the files in docs/wiki/"
echo "   2. Run: ./scripts/setup-github-wiki.sh"
echo ""
echo "💡 Tips:"
echo "   - Wiki pages support Markdown formatting"
echo "   - Use [[Page Name]] for internal links"
echo "   - Images can be uploaded directly to the wiki"
echo "   - Wiki history is preserved for all changes"
