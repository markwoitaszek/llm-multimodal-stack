# Project Automation Guide

## 🎯 Overview

This repository includes automated project management workflows that help maintain the project board status based on GitHub events. The automation ensures that issues move through the proper workflow stages automatically.

## 🔄 Automation Rules

### Issue Status Updates

The automation updates issue status based on PR events:

| PR Event | Target Branch | New Issue Status | Description |
|----------|---------------|------------------|-------------|
| **Opened/Ready for Review** | Any | `In Progress` | Issue moves to In Progress when work begins |
| **Merged** | `develop/*` or `dev/*` | `Ready to Release` | Issue ready for release when merged to development branch |
| **Merged** | `main` | `Done` | Issue completed when merged to main branch |

### How It Works

1. **PR Creation**: When a PR is opened that references an issue (using `fixes #123`, `resolves #123`, etc.), the linked issue automatically moves to `In Progress`.

2. **Development Merge**: When the PR is merged into a development branch (`develop/phase-1`, `dev/feature`, etc.), the linked issue moves to `Ready to Release`.

3. **Production Merge**: When the PR is merged into `main`, the linked issue moves to `Done`.

## 🎯 Project Board Columns

The automation works with these project board columns:

- **Todo**: New issues start here
- **In Progress**: Issues being worked on (PR created)
- **Ready to Release**: Issues completed in development branch
- **Done**: Issues completed and merged to main

## 🔧 Technical Details

### Workflow File
- **Location**: `.github/workflows/project-automation.yml`
- **Trigger**: PR events (opened, closed, ready_for_review, merged)

### Project Configuration
- **Project ID**: `PVT_kwHOAsUPVc4BEMuq` (LLM Multimodal Stack Development)
- **Status Field ID**: `PVTSSF_lAHOAsUPVc4BEMuqzg15RFE`
- **Status Options**:
  - Todo: `f75ad846`
  - In Progress: `47fc9ee4`
  - Ready to Release: `901b747a`
  - Done: `98236657`

### Issue Linking
The automation detects linked issues using these patterns in PR descriptions:
- `fixes #123`
- `closes #123`
- `resolves #123`
- `fix #123`
- `close #123`
- `resolve #123`

## 📋 Usage Examples

### Example 1: Feature Development
1. Create issue #45 for a new feature
2. Create PR with description: "Implements user authentication\n\nFixes #45"
3. Issue automatically moves to "In Progress"
4. Merge PR to `develop/phase-1`
5. Issue automatically moves to "Ready to Release"
6. Later, merge to `main` for production
7. Issue automatically moves to "Done"

### Example 2: Bug Fix
1. Create issue #67 for a bug
2. Create PR with description: "Fix container scan failures\n\nResolves #67"
3. Issue automatically moves to "In Progress"
4. Merge PR to `develop/phase-1`
5. Issue automatically moves to "Ready to Release"
6. When ready for production, merge to `main`
7. Issue automatically moves to "Done"

## 🚀 Benefits

### For Development Teams
- **Automated Tracking**: No manual project board updates needed
- **Clear Workflow**: Visual representation of development progress
- **Release Readiness**: Easy to see what's ready for release
- **Progress Visibility**: Stakeholders can see work status at a glance

### For Project Management
- **Accurate Status**: Issues always reflect current development state
- **Release Planning**: Clear view of what's ready for release
- **Progress Metrics**: Automated tracking of development velocity
- **Quality Gates**: Clear separation between development and production

## 🔍 Troubleshooting

### Issue Not Moving to "Ready to Release"
1. **Check PR Description**: Ensure the PR description includes `fixes #123` or similar
2. **Verify Branch**: PR must be merged to a development branch (`develop/*` or `dev/*`)
3. **Check Project**: Issue must be added to the project board
4. **Review Logs**: Check GitHub Actions logs for error messages

### Issue Not Moving to "Done"
1. **Check Branch**: PR must be merged to `main` branch
2. **Verify Merge**: Ensure the PR was actually merged, not just closed
3. **Check Permissions**: Ensure the workflow has proper permissions

### Manual Override
If automation fails, you can manually move issues:
1. Go to the project board
2. Drag the issue card to the desired column
3. The automation will respect manual changes

## 📊 Monitoring

### Workflow Logs
Check GitHub Actions logs for automation status:
1. Go to Actions tab in GitHub
2. Find "Project Automation" workflow
3. Click on the latest run
4. Review logs for any errors

### Project Board Status
Regularly review the project board to ensure:
- Issues are in the correct columns
- No issues are stuck in wrong states
- Release readiness is accurately reflected

## 🔧 Customization

### Adding New Status Columns
To add new status columns:
1. Add the column to the project board
2. Update the automation script with the new option ID
3. Add logic for when to use the new status

### Changing Branch Rules
To modify which branches trigger "Ready to Release":
1. Edit `.github/workflows/project-automation.yml`
2. Modify the `isDevBranch` logic
3. Update documentation

### Adding New Triggers
To add new automation triggers:
1. Add new event types to the workflow
2. Implement the logic in the appropriate job
3. Test thoroughly before deploying

---

**Last Updated**: $(date)  
**Workflow Version**: 2.0  
**Project ID**: PVT_kwHOAsUPVc4BEMuq
