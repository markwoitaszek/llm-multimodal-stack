#!/bin/bash

# Script to set up parent-child relationships using issue linking
# Usage: ./scripts/setup-issue-hierarchy.sh

set -e

echo "🔗 Setting up parent-child relationships using issue linking..."

# Define parent-child relationships
declare -A PARENT_CHILDREN=(
    ["27"]="3 4 5 18"      # Phase 1 Overview -> P1.3, P1.4, P1.5, P1.6
    ["28"]="6 7 8"         # Phase 2 Overview -> P2.1, P2.2, P2.3
    ["29"]="9 10"          # Phase 3 Overview -> P3.1, P3.2
    ["30"]="21 22 23 24 25 26"  # Phase 4 Overview -> P4.1, P4.2, P4.3, P4.4, P4.5, P4.6
)

# Function to link child to parent
link_child_to_parent() {
    local child_issue=$1
    local parent_issue=$2
    
    echo "🔗 Linking Issue #$child_issue to parent Issue #$parent_issue..."
    
    # Get issue titles for better context
    local child_title=$(gh issue view $child_issue --json title -q '.title')
    local parent_title=$(gh issue view $parent_issue --json title -q '.title')
    
    # Create a comment linking the issues
    local comment="🔗 **Parent Issue**: This issue is part of the implementation for #$parent_issue
    
**Parent**: $parent_title
**Child**: $child_title

This creates a hierarchical relationship between the phase overview and its implementation issues."
    
    # Add the comment to the child issue
    gh issue comment $child_issue --body "$comment"
    
    echo "✅ Successfully linked Issue #$child_issue to parent Issue #$parent_issue"
}

# Function to update parent issue with children list
update_parent_with_children() {
    local parent_issue=$1
    local children_list="$2"
    
    echo "📋 Updating parent Issue #$parent_issue with children list..."
    
    # Get parent issue title
    local parent_title=$(gh issue view $parent_issue --json title -q '.title')
    
    # Create children list
    local children_links=""
    for child in $children_list; do
        local child_title=$(gh issue view $child --json title -q '.title')
        children_links+="- #$child - $child_title\n"
    done
    
    # Create a comment with the children list
    local comment="📋 **Implementation Issues** (Children):

$children_links

These issues implement the requirements outlined in this phase overview."
    
    # Add the comment to the parent issue
    gh issue comment $parent_issue --body "$comment"
    
    echo "✅ Successfully updated parent Issue #$parent_issue with children list"
}

# Set up all parent-child relationships
for parent in "${!PARENT_CHILDREN[@]}"; do
    children="${PARENT_CHILDREN[$parent]}"
    echo ""
    echo "📋 Setting up hierarchy for Phase Overview Issue #$parent:"
    
    # Update parent with children list
    update_parent_with_children $parent "$children"
    
    # Link each child to parent
    for child in $children; do
        link_child_to_parent $child $parent
    done
done

echo ""
echo "🎉 All parent-child relationships have been set up successfully!"
echo ""
echo "📊 Summary:"
echo "   Phase 1 Overview (#27) → 4 implementation issues"
echo "   Phase 2 Overview (#28) → 3 implementation issues"
echo "   Phase 3 Overview (#29) → 2 implementation issues"
echo "   Phase 4 Overview (#30) → 6 implementation issues"
echo ""
echo "🔍 You can now see the relationships in the issue comments and GitHub's issue linking!"
