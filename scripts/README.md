# Development Workflow Scripts

This directory contains scripts to help manage the development workflow with automatic branch creation using GitHub Projects.

## 🚀 Automatic Branch Creation Workflow

When you start work on an issue, GitHub Actions will automatically create a branch for you based on the issue type and milestone.

### How It Works

1. **Set issue status to "In Progress"** in the GitHub Project (manually or via script)
2. **GitHub Actions triggers** and creates a branch automatically
3. **Branch is created** with appropriate naming and documentation
4. **Issue is commented** with branch details and next steps

### GitHub Project Integration

We use a GitHub Project with three status states:
- **Todo** - Issues that need to be worked on
- **In Progress** - Issues currently being worked on (triggers branch creation)
- **Done** - Completed issues

### Branch Naming Convention

- **Phase Overview Issues**: `dev/phase-X` (e.g., `dev/phase-2`)
- **Feature Issues**: `feature/issue-XXX-description` (e.g., `feature/issue-6-mcp-support`)

## 📋 Available Scripts

### `start-work.sh` - Start Working on an Issue

```bash
./scripts/start-work.sh <issue-number>
```

**Example:**
```bash
# Start work on Phase 2 overview
./scripts/start-work.sh 28

# Start work on MCP support feature
./scripts/start-work.sh 6
```

**What it does:**
- Sets issue status to "In Progress" in the GitHub Project
- Triggers automatic branch creation
- Shows expected branch name
- Provides next steps

### `stop-work.sh` - Stop Working on an Issue

```bash
./scripts/stop-work.sh <issue-number>
```

**Example:**
```bash
# Stop work on an issue
./scripts/stop-work.sh 6
```

**What it does:**
- Sets issue status to "Done" or "Todo" in the GitHub Project
- Optionally closes the issue if work is complete
- Provides feedback on next steps

## 🎯 Typical Workflow

### Starting a Phase

1. **Start Phase Overview Issue:**
   ```bash
   ./scripts/start-work.sh 28  # Phase 2 Overview
   ```
   - Creates `dev/phase-2` branch
   - Sets up phase coordination

2. **Start Individual Features:**
   ```bash
   ./scripts/start-work.sh 6   # P2.1 MCP Support
   ./scripts/start-work.sh 7   # P2.2 Advanced Search
   ./scripts/start-work.sh 8   # P2.3 User Management
   ```
   - Creates feature branches like `feature/issue-6-mcp-support`
   - Each branch is ready for development

### Development Process

1. **Checkout the created branch:**
   ```bash
   git checkout dev/phase-2
   # or
   git checkout feature/issue-6-mcp-support
   ```

2. **Make your changes and commit:**
   ```bash
   git add .
   git commit -m "Implement MCP protocol support"
   git push origin feature/issue-6-mcp-support
   ```

3. **Create Pull Request:**
   - Feature branches → Phase branch
   - Phase branch → Main branch

4. **Stop work when complete:**
   ```bash
   ./scripts/stop-work.sh 6
   ```

## 🔧 Manual Workflow (Alternative)

If you prefer to work manually:

1. **Go to the GitHub Project** (https://github.com/users/markwoitaszek/projects/8)
2. **Drag the issue** from "Todo" to "In Progress" column
3. **Wait for GitHub Actions** to create the branch
4. **Check the issue comments** for branch details
5. **Checkout and work** on the created branch

## 🔗 Parent-Child Issue Relationships

The project uses a hierarchical structure where overview issues are parents to their implementation issues:

### **Hierarchy Structure**
```
Phase 1 Overview (#27)
├── P1.4 Software Stack Modernization (#4)
├── P1.5 Comprehensive Test Suite (#5)
└── P1.6 Documentation & Wiki (#18)

Phase 2 Overview (#28)
├── P2.1 MCP Support (#6)
├── P2.2 Advanced Search (#7)
└── P2.3 User Management (#8)

Phase 3 Overview (#29)
├── P3.1 Analytics Dashboard (#9)
└── P3.2 API Connectors (#10)

Phase 4 Overview (#30)
├── P4.1 IDE Integration Foundation (#21)
├── P4.2 Agent Framework Core (#22)
├── P4.3 Workflow Automation (#23)
├── P4.4 Agent Dashboard (#24)
├── P4.5 Protocol Integration (#25)
└── P4.6 Real-Time Collaboration (#26)
```

### **Setting Up Relationships**
Use the provided scripts to establish parent-child relationships:

```bash
# Set up issue linking (comments with relationships)
./scripts/setup-issue-hierarchy.sh

# Add all issues to the GitHub Project
./scripts/add-issues-to-project-rest.sh
```

## 📝 Branch Structure

```
main
├── dev/phase-1          # Phase 1 development
├── dev/phase-2          # Phase 2 development
│   ├── feature/issue-6-mcp-support
│   ├── feature/issue-7-advanced-search
│   └── feature/issue-8-user-management
├── dev/phase-3          # Phase 3 development
└── dev/phase-4          # Phase 4 development
```

## 🚨 Troubleshooting

### Branch Already Exists
If you try to start work on an issue that already has a branch:
- The script will inform you the branch exists
- Check the issue comments for the branch name
- Simply checkout the existing branch

### GitHub Actions Not Triggering
- Ensure the issue is in the GitHub Project
- Check that the status is set to "In Progress"
- Check the Actions tab in GitHub for workflow status
- Verify the workflow file is in `.github/workflows/`

### Wrong Branch Name
- Branch names are automatically generated based on issue title
- Special characters are cleaned up automatically
- Phase branches use milestone information

## 🎉 Benefits

- **Automatic branch creation** saves time
- **Consistent naming** across the project
- **Documentation included** in each branch
- **Clear workflow** for team collaboration
- **Integration with GitHub** for seamless development
