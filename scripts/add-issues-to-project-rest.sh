#!/bin/bash

# Script to add all issues to the GitHub Project using REST API
# Usage: ./scripts/add-issues-to-project-rest.sh

set -e

echo "📋 Adding all issues to the GitHub Project using REST API..."

# Get project data
PROJECT_DATA=$(gh api graphql -f query='
query($owner: String!) {
  user(login: $owner) {
    projectV2(number: 8) {
      id
    }
  }
}' -f owner="markwoitaszek")

PROJECT_ID=$(echo $PROJECT_DATA | jq -r '.data.user.projectV2.id')

echo "📋 Project ID: $PROJECT_ID"
echo ""

# List of all issues to add (in order from the issue list)
ISSUES=(4 5 6 7 8 9 10 18 21 22 23 24 25 26 27 28 29 30 31 32)

# Function to add issue to project using REST API
add_issue_to_project() {
    local issue_number=$1
    
    echo "➕ Adding Issue #$issue_number to project..."
    
    # Get issue details using REST API
    local issue_data=$(gh api repos/markwoitaszek/llm-multimodal-stack/issues/$issue_number)
    local issue_id=$(echo $issue_data | jq -r '.node_id')
    
    if [[ -z "$issue_id" || "$issue_id" == "null" ]]; then
        echo "❌ Could not find Issue #$issue_number. Skipping..."
        return 1
    fi
    
    # Add issue to project using GraphQL
    gh api graphql -f query='
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }' -f projectId="$PROJECT_ID" -f contentId="$issue_id" > /dev/null
    
    echo "✅ Successfully added Issue #$issue_number to project"
}

# Add all issues to project
for issue in "${ISSUES[@]}"; do
    add_issue_to_project $issue
done

echo ""
echo "🎉 All issues have been added to the GitHub Project!"
echo ""
echo "📊 Added ${#ISSUES[@]} issues to the project"
echo "🔍 You can now see all issues in your GitHub Project board!"
