#!/bin/bash

# Script to start work on an issue by setting project status to "In Progress"
# Usage: ./scripts/start-work.sh <issue-number>
# Example: ./scripts/start-work.sh 28

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <issue-number>"
    echo "Example: $0 28"
    echo ""
    echo "This script will:"
    echo "1. Set the issue status to 'In Progress' in the GitHub Project"
    echo "2. Trigger automatic branch creation via GitHub Actions"
    echo "3. Show you the branch name that will be created"
    exit 1
fi

ISSUE_NUMBER=$1

echo "🚀 Starting work on Issue #$ISSUE_NUMBER..."

# Get issue details
ISSUE_INFO=$(gh issue view $ISSUE_NUMBER --json title,milestone,labels)

ISSUE_TITLE=$(echo $ISSUE_INFO | jq -r '.title')
MILESTONE=$(echo $ISSUE_INFO | jq -r '.milestone.title // "No milestone"')
LABELS=$(echo $ISSUE_INFO | jq -r '.labels[].name' | tr '\n' ', ' | sed 's/,$//')

echo "📋 Issue Details:"
echo "   Title: $ISSUE_TITLE"
echo "   Milestone: $MILESTONE"
echo "   Current Labels: $LABELS"
echo ""

# Check if issue is already in the project and get current status
echo "🔍 Checking project status..."
PROJECT_STATUS=$(gh api graphql -f query='
query($owner: String!, $repo: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      projectItems(first: 10) {
        nodes {
          project {
            title
          }
          fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue {
              name
            }
          }
        }
      }
    }
  }
}' -f owner="markwoitaszek" -f repo="llm-multimodal-stack" -f issueNumber="$ISSUE_NUMBER" | jq -r '.data.repository.issue.projectItems.nodes[0].fieldValueByName.name // "Not in project"')

echo "   Current Project Status: $PROJECT_STATUS"

if [[ "$PROJECT_STATUS" == "In Progress" ]]; then
    echo "⚠️  Issue #$ISSUE_NUMBER is already marked as 'In Progress' in the project"
    echo "   The branch should already exist. Check the issue comments for the branch name."
    exit 0
fi

# Add issue to project if not already there, and set status to "In Progress"
echo "📋 Setting project status to 'In Progress'..."

# First, get the project ID and field IDs
PROJECT_DATA=$(gh api graphql -f query='
query($owner: String!) {
  user(login: $owner) {
    projectV2(number: 8) {
      id
      fields(first: 20) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
        }
      }
    }
  }
}' -f owner="markwoitaszek")

PROJECT_ID=$(echo $PROJECT_DATA | jq -r '.data.user.projectV2.id')
STATUS_FIELD_ID=$(echo $PROJECT_DATA | jq -r '.data.user.projectV2.fields.nodes[] | select(.name == "Status") | .id')
IN_PROGRESS_OPTION_ID=$(echo $PROJECT_DATA | jq -r '.data.user.projectV2.fields.nodes[] | select(.name == "Status") | .options[] | select(.name == "In Progress") | .id')

# Add issue to project and set status
gh api graphql -f query='
mutation($projectId: ID!, $contentId: ID!, $fieldId: ID!, $optionId: String!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item {
      id
    }
  }
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId
    itemId: $itemId
    fieldId: $fieldId
    value: {singleSelectOptionId: $optionId}
  }) {
    projectV2Item {
      id
    }
  }
}' -f projectId="$PROJECT_ID" -f contentId="$(gh api graphql -f query='query($owner: String!, $repo: String!, $issueNumber: Int!) { repository(owner: $owner, name: $repo) { issue(number: $issueNumber) { id } } }' -f owner="markwoitaszek" -f repo="llm-multimodal-stack" -f issueNumber="$ISSUE_NUMBER" | jq -r '.data.repository.issue.id')" -f fieldId="$STATUS_FIELD_ID" -f optionId="$IN_PROGRESS_OPTION_ID" > /dev/null

echo "✅ Successfully set Issue #$ISSUE_NUMBER status to 'In Progress' in the project"
echo ""
echo "🔄 GitHub Actions will now automatically:"
echo "   1. Create a new branch for this issue"
echo "   2. Add documentation to the branch"
echo "   3. Comment on the issue with branch details"
echo ""
echo "⏳ Please wait a moment for the workflow to complete..."
echo "   You can check the Actions tab in GitHub or the issue comments for updates."
echo ""
echo "📝 Expected branch naming:"
if [[ "$ISSUE_TITLE" == *"Overview"* ]]; then
    PHASE_NUM=$(echo "$MILESTONE" | grep -o 'Phase [0-9]' | grep -o '[0-9]')
    echo "   Phase branch: dev/phase-$PHASE_NUM"
else
    CLEAN_TITLE=$(echo "$ISSUE_TITLE" | sed 's/\[.*\]//g' | sed 's/[^a-zA-Z0-9 -]//g' | sed 's/  */ /g' | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
    echo "   Feature branch: feature/issue-$ISSUE_NUMBER-$CLEAN_TITLE"
fi
