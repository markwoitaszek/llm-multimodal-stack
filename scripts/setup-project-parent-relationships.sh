#!/bin/bash

# Script to set up parent-child relationships in the GitHub Project
# Usage: ./scripts/setup-project-parent-relationships.sh

set -e

echo "🔗 Setting up parent-child relationships in the GitHub Project..."

# Get project data
PROJECT_DATA=$(gh api graphql -f query='
query($owner: String!) {
  user(login: $owner) {
    projectV2(number: 8) {
      id
      fields(first: 20) {
        nodes {
          ... on ProjectV2Field {
            id
            name
          }
        }
      }
    }
  }
}' -f owner="markwoitaszek")

PROJECT_ID=$(echo $PROJECT_DATA | jq -r '.data.user.projectV2.id')
PARENT_FIELD_ID=$(echo $PROJECT_DATA | jq -r '.data.user.projectV2.fields.nodes[] | select(.name == "Parent issue") | .id')

echo "📋 Project ID: $PROJECT_ID"
echo "📋 Parent Field ID: $PARENT_FIELD_ID"
echo ""

# Define parent-child relationships (updated with correct issue numbers)
declare -A PARENT_CHILDREN=(
    ["27"]="4 5 18"        # Phase 1 Overview -> P1.4, P1.5, P1.6
    ["28"]="6 7 8"         # Phase 2 Overview -> P2.1, P2.2, P2.3
    ["29"]="9 10"          # Phase 3 Overview -> P3.1, P3.2
    ["30"]="21 22 23 24 25 26"  # Phase 4 Overview -> P4.1, P4.2, P4.3, P4.4, P4.5, P4.6
)

# Function to get issue node ID using REST API
get_issue_node_id() {
    local issue_number=$1
    gh api repos/markwoitaszek/llm-multimodal-stack/issues/$issue_number | jq -r '.node_id'
}

# Function to get project item ID
get_project_item_id() {
    local issue_number=$1
    gh api graphql -f query='
    query($owner: String!, $repo: String!, $issueNumber: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $issueNumber) {
          projectItems(first: 10) {
            nodes {
              id
              project {
                title
              }
            }
          }
        }
      }
    }' -f owner="markwoitaszek" -f repo="llm-multimodal-stack" -f issueNumber="$issue_number" | jq -r '.data.repository.issue.projectItems.nodes[0].id // empty'
}

# Function to set parent relationship
set_parent_relationship() {
    local child_issue=$1
    local parent_issue=$2
    
    echo "🔗 Setting Issue #$child_issue as child of Issue #$parent_issue..."
    
    # Get the project item ID for the child issue
    local child_item_id=$(get_project_item_id $child_issue)
    
    if [[ -z "$child_item_id" || "$child_item_id" == "null" ]]; then
        echo "❌ Could not get project item ID for Issue #$child_issue. Skipping..."
        return 1
    fi
    
    # Set the parent relationship
    local parent_issue_id=$(get_issue_node_id $parent_issue)
    if [[ -z "$parent_issue_id" || "$parent_issue_id" == "null" ]]; then
        echo "❌ Could not find parent Issue #$parent_issue. Skipping..."
        return 1
    fi
    
    gh api graphql -f query='
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId
        itemId: $itemId
        fieldId: $fieldId
        value: {text: $value}
      }) {
        projectV2Item {
          id
        }
      }
    }' -f projectId="$PROJECT_ID" -f itemId="$child_item_id" -f fieldId="$PARENT_FIELD_ID" -f value="$parent_issue_id" > /dev/null
    
    echo "✅ Successfully set Issue #$child_issue as child of Issue #$parent_issue"
}

# Set up all parent-child relationships
for parent in "${!PARENT_CHILDREN[@]}"; do
    children="${PARENT_CHILDREN[$parent]}"
    echo ""
    echo "📋 Setting up children for Phase Overview Issue #$parent:"
    
    for child in $children; do
        set_parent_relationship $child $parent
    done
done

echo ""
echo "🎉 All parent-child relationships have been set up successfully!"
echo ""
echo "📊 Summary:"
echo "   Phase 1 Overview (#27) → 3 implementation issues"
echo "   Phase 2 Overview (#28) → 3 implementation issues"
echo "   Phase 3 Overview (#29) → 2 implementation issues"
echo "   Phase 4 Overview (#30) → 6 implementation issues"
echo ""
echo "🔍 You can now see the hierarchy in your GitHub Project board!"
