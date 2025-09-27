#!/bin/bash

# Script to add all issues to the GitHub Project
# Usage: ./scripts/add-issues-to-project.sh

set -e

echo "📋 Adding all issues to the GitHub Project..."

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

# Function to add issue to project
add_issue_to_project() {
    local issue_number=$1
    
    echo "➕ Adding Issue #$issue_number to project..."
    
    # Get issue node ID
    local issue_id=$(gh api graphql -f query='
    query($owner: String!, $repo: String!, $issueNumber: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $issueNumber) {
          id
        }
      }
    }' -f owner="markwoitaszek" -f repo="llm-multimodal-stack" -f issueNumber="$issue_number" | jq -r '.data.repository.issue.id')
    
    if [[ -z "$issue_id" || "$issue_id" == "null" ]]; then
        echo "❌ Could not find Issue #$issue_number. Skipping..."
        return 1
    fi
    
    # Add issue to project
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
