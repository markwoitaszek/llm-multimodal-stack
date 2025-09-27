#!/bin/bash
set -e

# GitHub Wiki Manual Setup Script for Multimodal LLM Stack
echo "📚 Setting up GitHub Wiki documentation (Manual Method)..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from the project root."
    exit 1
fi

# Get repository information
REPO_URL=$(git remote get-url origin)
REPO_NAME=$(basename "$REPO_URL" .git)

echo "📋 Repository: $REPO_NAME"
echo "🔗 Wiki will be available at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^/]*\)\.git.*/\1\/\2/')/wiki"

echo ""
echo "🔧 Manual Wiki Setup Instructions:"
echo "=================================="
echo ""
echo "1. Enable Wiki in GitHub Repository Settings:"
echo "   - Go to: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^/]*\)\.git.*/\1\/\2/')/settings"
echo "   - Scroll down to 'Features' section"
echo "   - Check the 'Wikis' checkbox"
echo "   - Click 'Save changes'"
echo ""
echo "2. Clone the Wiki Repository:"
echo "   git clone https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^/]*\)\.git.*/\1\/\2/').wiki.git"
echo ""
echo "3. Copy Wiki Content:"
echo "   cp docs/wiki/*.md $(basename "$REPO_URL" .git).wiki/"
echo "   cp docs/*.md $(basename "$REPO_URL" .git).wiki/"
echo ""
echo "4. Commit and Push Wiki Changes:"
echo "   cd $(basename "$REPO_URL" .git).wiki"
echo "   git add ."
echo "   git commit -m 'Add comprehensive wiki documentation'"
echo "   git push origin master"
echo ""

# Create a temporary directory with all wiki content
TEMP_WIKI_DIR="temp-wiki-content"
echo "📁 Creating temporary wiki content directory: $TEMP_WIKI_DIR"
mkdir -p "$TEMP_WIKI_DIR"

# Copy wiki content
echo "📄 Copying wiki content..."
cp docs/wiki/*.md "$TEMP_WIKI_DIR/" 2>/dev/null || echo "⚠️  No wiki-specific files found"

# Copy additional documentation
echo "📚 Copying additional documentation..."
for doc in docs/*.md; do
    if [ -f "$doc" ]; then
        # Convert filename to wiki format
        wiki_name=$(basename "$doc" .md)
        # Convert to title case with dashes
        wiki_name=$(echo "$wiki_name" | sed 's/\([A-Z]\)/-\1/g' | sed 's/^-//' | tr '[:upper:]' '[:lower:]' | sed 's/^\(.\)/\U\1/')
        cp "$doc" "$TEMP_WIKI_DIR/$wiki_name.md"
        echo "   ✅ Copied: $doc -> $wiki_name.md"
    fi
done

echo ""
echo "📋 Wiki Content Summary:"
echo "======================="
echo ""
echo "Files ready for wiki upload:"
for file in "$TEMP_WIKI_DIR"/*.md; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "   - $filename"
    fi
done

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo ""
echo "Option 1: Manual Upload (Recommended)"
echo "1. Go to your GitHub repository"
echo "2. Click on the 'Wiki' tab"
echo "3. Click 'Create the first page'"
echo "4. For each file in $TEMP_WIKI_DIR/, create a new page with the content"
echo ""
echo "Option 2: Clone Wiki Repository"
echo "1. Enable wiki in repository settings"
echo "2. Clone the wiki repository"
echo "3. Copy files from $TEMP_WIKI_DIR/ to the cloned wiki"
echo "4. Commit and push changes"
echo ""
echo "📚 Wiki Pages to Create:"
echo "======================="
for file in "$TEMP_WIKI_DIR"/*.md; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .md)
        echo "   - $filename"
    fi
done

echo ""
echo "🔗 Your wiki will be available at:"
echo "   https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^/]*\)\.git.*/\1\/\2/')/wiki"
echo ""
echo "💡 Tips:"
echo "   - Use [[Page Name]] for internal wiki links"
echo "   - Images can be uploaded directly to the wiki"
echo "   - Wiki history is preserved for all changes"
echo ""
echo "🎉 Wiki content is ready in: $TEMP_WIKI_DIR/"
echo "   You can now manually upload these files to your GitHub wiki."
