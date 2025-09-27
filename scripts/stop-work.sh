#!/bin/bash

# Script to stop work on an issue by setting project status to "Done" or "Todo"
# Usage: ./scripts/stop-work.sh <issue-number>
# Example: ./scripts/stop-work.sh 28

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <issue-number>"
    echo "Example: $0 28"
    echo ""
    echo "This script will:"
    echo "1. Set the issue status to 'Done' or 'Todo' in the GitHub Project"
    echo "2. Optionally close the issue if work is complete"
    exit 1
fi

ISSUE_NUMBER=$1

echo "🛑 Stopping work on Issue #$ISSUE_NUMBER..."

# Get issue details
ISSUE_INFO=$(gh issue view $ISSUE_NUMBER --json title,milestone,labels,state)

ISSUE_TITLE=$(echo $ISSUE_INFO | jq -r '.title')
MILESTONE=$(echo $ISSUE_INFO | jq -r '.milestone.title // "No milestone"')
LABELS=$(echo $ISSUE_INFO | jq -r '.labels[].name' | tr '\n' ', ' | sed 's/,$//')
STATE=$(echo $ISSUE_INFO | jq -r '.state')

echo "📋 Issue Details:"
echo "   Title: $ISSUE_TITLE"
echo "   Milestone: $MILESTONE"
echo "   State: $STATE"
echo "   Current Labels: $LABELS"
echo ""

# Check current project status
echo "🔍 Checking current project status..."
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

if [[ "$PROJECT_STATUS" != "In Progress" ]]; then
    echo "ℹ️  Issue #$ISSUE_NUMBER is not currently marked as 'In Progress' in the project"
    exit 0
fi

# Ask if work is complete
echo ""
read -p "🤔 Is the work on this issue complete? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🎉 Marking issue as complete..."
    NEW_STATUS="Done"
    
    # Get project data
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
    DONE_OPTION_ID=$(echo $PROJECT_DATA | jq -r '.data.user.projectV2.fields.nodes[] | select(.name == "Status") | .options[] | select(.name == "Done") | .id')
    
    # Update project status to Done
    gh api graphql -f query='
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
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
    }' -f projectId="$PROJECT_ID" -f itemId="$(gh api graphql -f query='query($owner: String!, $repo: String!, $issueNumber: Int!) { repository(owner: $owner, name: $repo) { issue(number: $issueNumber) { projectItems(first: 10) { nodes { id } } } } }' -f owner="markwoitaszek" -f repo="llm-multimodal-stack" -f issueNumber="$ISSUE_NUMBER" | jq -r '.data.repository.issue.projectItems.nodes[0].id')" -f fieldId="$STATUS_FIELD_ID" -f optionId="$DONE_OPTION_ID" > /dev/null
    
    echo "✅ Successfully set Issue #$ISSUE_NUMBER status to 'Done' in the project"
    
    # Ask if should close the issue
    read -p "🔒 Should we close the issue as well? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔒 Closing issue..."
        gh issue close $ISSUE_NUMBER --comment "Work completed successfully! 🎉"
        echo "✅ Issue #$ISSUE_NUMBER has been closed"
    else
        echo "📝 Issue #$ISSUE_NUMBER remains open but marked as done in the project"
    fi
else
    echo "📝 Moving issue back to 'Todo' status..."
    NEW_STATUS="Todo"
    
    # Get project data
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
    TODO_OPTION_ID=$(echo $PROJECT_DATA | jq -r '.data.user.projectV2.fields.nodes[] | select(.name == "Status") | .options[] | select(.name == "Todo") | .id')
    
    # Update project status to Todo
    gh api graphql -f query='
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
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
    }' -f projectId="$PROJECT_ID" -f itemId="$(gh api graphql -f query='query($owner: String!, $repo: String!, $issueNumber: Int!) { repository(owner: $owner, name: $repo) { issue(number: $issueNumber) { projectItems(first: 10) { nodes { id } } } } }' -f owner="markwoitaszek" -f repo="llm-multimodal-stack" -f issueNumber="$ISSUE_NUMBER" | jq -r '.data.repository.issue.projectItems.nodes[0].id')" -f fieldId="$STATUS_FIELD_ID" -f optionId="$TODO_OPTION_ID" > /dev/null
    
    echo "✅ Successfully set Issue #$ISSUE_NUMBER status to 'Todo' in the project"
    echo "📝 Issue #$ISSUE_NUMBER is ready for future work"
    echo "   You can restart work anytime by running: ./scripts/start-work.sh $ISSUE_NUMBER"
fi
