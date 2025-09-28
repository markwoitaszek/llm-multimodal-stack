#!/usr/bin/env python3
"""
API Version Management System
Part of Issue #46: API Lifecycle Management

This module provides comprehensive API version management including:
- Version creation and management
- Migration strategies and tools
- Backward compatibility handling
- Version deprecation and sunset policies
- Change tracking and documentation
"""

import asyncio
import json
import yaml
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path
import hashlib
import semver
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VersionStatus(Enum):
    """API version status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    ARCHIVED = "archived"

class ChangeType(Enum):
    """Change type enumeration"""
    BREAKING = "breaking"
    ADDITIVE = "additive"
    FIX = "fix"
    DEPRECATION = "deprecation"
    REMOVAL = "removal"

class MigrationStrategy(Enum):
    """Migration strategy enumeration"""
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    SCHEDULED = "scheduled"
    MANUAL = "manual"

@dataclass
class APIChange:
    """Represents a change in API"""
    change_id: str
    change_type: ChangeType
    description: str
    affected_endpoints: List[str]
    breaking_changes: List[str] = field(default_factory=list)
    migration_notes: str = ""
    impact_level: str = "low"  # low, medium, high, critical
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class APIVersion:
    """Represents an API version"""
    version: str
    status: VersionStatus
    created_date: str
    release_date: Optional[str] = None
    deprecation_date: Optional[str] = None
    sunset_date: Optional[str] = None
    description: str = ""
    changes: List[APIChange] = field(default_factory=list)
    endpoints: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    schemas: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    migration_guide: str = ""
    backward_compatible: bool = True
    parent_version: Optional[str] = None

@dataclass
class VersionPolicy:
    """Version management policy"""
    policy_id: str
    name: str
    description: str
    deprecation_period_days: int = 90
    sunset_period_days: int = 180
    max_active_versions: int = 3
    auto_deprecate: bool = True
    require_migration_guide: bool = True
    breaking_change_notice_days: int = 30

class VersionManager:
    """Manages API versions and lifecycle"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Version storage
        self.versions: Dict[str, APIVersion] = {}
        self.policies: Dict[str, VersionPolicy] = {}
        self.migration_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.version_file = self.data_dir / "versions.json"
        self.policies_file = self.data_dir / "policies.json"
        self.migration_file = self.data_dir / "migrations.json"
        
        # Load existing data
        self._load_data()
        
        # Initialize default policy if none exists
        if not self.policies:
            self._create_default_policy()
    
    def _load_data(self):
        """Load version data from files"""
        try:
            # Load versions
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    for version_str, version_data in data.items():
                        version_data['status'] = VersionStatus(version_data['status'])
                        version_data['changes'] = [
                            APIChange(**change) for change in version_data.get('changes', [])
                        ]
                        self.versions[version_str] = APIVersion(**version_data)
            
            # Load policies
            if self.policies_file.exists():
                with open(self.policies_file, 'r') as f:
                    data = json.load(f)
                    for policy_id, policy_data in data.items():
                        self.policies[policy_id] = VersionPolicy(**policy_data)
            
            # Load migration history
            if self.migration_file.exists():
                with open(self.migration_file, 'r') as f:
                    self.migration_history = json.load(f)
            
            logger.info(f"Loaded {len(self.versions)} versions and {len(self.policies)} policies")
            
        except Exception as e:
            logger.error(f"Error loading version data: {e}")
    
    def _save_data(self):
        """Save version data to files"""
        try:
            # Save versions
            versions_data = {}
            for version_str, version in self.versions.items():
                version_dict = asdict(version)
                version_dict['status'] = version.status.value
                version_dict['changes'] = [asdict(change) for change in version.changes]
                versions_data[version_str] = version_dict
            
            with open(self.version_file, 'w') as f:
                json.dump(versions_data, f, indent=2)
            
            # Save policies
            policies_data = {policy_id: asdict(policy) for policy_id, policy in self.policies.items()}
            with open(self.policies_file, 'w') as f:
                json.dump(policies_data, f, indent=2)
            
            # Save migration history
            with open(self.migration_file, 'w') as f:
                json.dump(self.migration_history, f, indent=2)
            
            logger.info("Version data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving version data: {e}")
    
    def _create_default_policy(self):
        """Create default version policy"""
        default_policy = VersionPolicy(
            policy_id="default",
            name="Default Version Policy",
            description="Default policy for API version management",
            deprecation_period_days=90,
            sunset_period_days=180,
            max_active_versions=3,
            auto_deprecate=True,
            require_migration_guide=True,
            breaking_change_notice_days=30
        )
        
        self.policies["default"] = default_policy
        self._save_data()
    
    def create_version(
        self,
        version: str,
        description: str = "",
        parent_version: Optional[str] = None,
        policy_id: str = "default"
    ) -> APIVersion:
        """Create a new API version"""
        # Validate version format
        try:
            semver.VersionInfo.parse(version)
        except ValueError:
            raise ValueError(f"Invalid version format: {version}")
        
        # Check if version already exists
        if version in self.versions:
            raise ValueError(f"Version {version} already exists")
        
        # Get policy
        policy = self.policies.get(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        
        # Check max active versions
        active_versions = [v for v in self.versions.values() if v.status == VersionStatus.ACTIVE]
        if len(active_versions) >= policy.max_active_versions:
            raise ValueError(f"Maximum active versions ({policy.max_active_versions}) exceeded")
        
        # Create new version
        api_version = APIVersion(
            version=version,
            status=VersionStatus.DRAFT,
            created_date=datetime.now().isoformat(),
            description=description,
            parent_version=parent_version
        )
        
        self.versions[version] = api_version
        self._save_data()
        
        logger.info(f"Created new API version: {version}")
        return api_version
    
    def add_change(
        self,
        version: str,
        change_type: ChangeType,
        description: str,
        affected_endpoints: List[str],
        breaking_changes: List[str] = None,
        migration_notes: str = "",
        impact_level: str = "low"
    ) -> APIChange:
        """Add a change to a version"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not found")
        
        change = APIChange(
            change_id=str(uuid.uuid4()),
            change_type=change_type,
            description=description,
            affected_endpoints=affected_endpoints,
            breaking_changes=breaking_changes or [],
            migration_notes=migration_notes,
            impact_level=impact_level
        )
        
        self.versions[version].changes.append(change)
        
        # Update backward compatibility
        if change_type == ChangeType.BREAKING:
            self.versions[version].backward_compatible = False
        
        self._save_data()
        
        logger.info(f"Added {change_type.value} change to version {version}")
        return change
    
    def release_version(self, version: str, release_date: Optional[str] = None) -> APIVersion:
        """Release a version (move from draft to active)"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not found")
        
        api_version = self.versions[version]
        
        if api_version.status != VersionStatus.DRAFT:
            raise ValueError(f"Version {version} is not in draft status")
        
        # Set release date
        api_version.release_date = release_date or datetime.now().isoformat()
        api_version.status = VersionStatus.ACTIVE
        
        self._save_data()
        
        logger.info(f"Released version {version}")
        return api_version
    
    def deprecate_version(
        self,
        version: str,
        deprecation_date: Optional[str] = None,
        policy_id: str = "default"
    ) -> APIVersion:
        """Deprecate a version"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not found")
        
        api_version = self.versions[version]
        
        if api_version.status != VersionStatus.ACTIVE:
            raise ValueError(f"Version {version} is not active")
        
        # Get policy
        policy = self.policies.get(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        
        # Set deprecation date
        api_version.deprecation_date = deprecation_date or datetime.now().isoformat()
        api_version.status = VersionStatus.DEPRECATED
        
        # Calculate sunset date
        if policy.sunset_period_days > 0:
            dep_date = datetime.fromisoformat(api_version.deprecation_date)
            sunset_date = dep_date + timedelta(days=policy.sunset_period_days)
            api_version.sunset_date = sunset_date.isoformat()
        
        self._save_data()
        
        logger.info(f"Deprecated version {version}")
        return api_version
    
    def sunset_version(self, version: str) -> APIVersion:
        """Sunset a version (move from deprecated to sunset)"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not found")
        
        api_version = self.versions[version]
        
        if api_version.status != VersionStatus.DEPRECATED:
            raise ValueError(f"Version {version} is not deprecated")
        
        api_version.status = VersionStatus.SUNSET
        
        self._save_data()
        
        logger.info(f"Sunset version {version}")
        return api_version
    
    def archive_version(self, version: str) -> APIVersion:
        """Archive a version (move from sunset to archived)"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not found")
        
        api_version = self.versions[version]
        
        if api_version.status != VersionStatus.SUNSET:
            raise ValueError(f"Version {version} is not sunset")
        
        api_version.status = VersionStatus.ARCHIVED
        
        self._save_data()
        
        logger.info(f"Archived version {version}")
        return api_version
    
    def get_version(self, version: str) -> Optional[APIVersion]:
        """Get a specific version"""
        return self.versions.get(version)
    
    def list_versions(self, status: Optional[VersionStatus] = None) -> List[APIVersion]:
        """List versions, optionally filtered by status"""
        versions = list(self.versions.values())
        
        if status:
            versions = [v for v in versions if v.status == status]
        
        # Sort by version number
        versions.sort(key=lambda v: semver.VersionInfo.parse(v.version), reverse=True)
        
        return versions
    
    def get_active_versions(self) -> List[APIVersion]:
        """Get all active versions"""
        return self.list_versions(VersionStatus.ACTIVE)
    
    def get_deprecated_versions(self) -> List[APIVersion]:
        """Get all deprecated versions"""
        return self.list_versions(VersionStatus.DEPRECATED)
    
    def get_latest_version(self) -> Optional[APIVersion]:
        """Get the latest active version"""
        active_versions = self.get_active_versions()
        return active_versions[0] if active_versions else None
    
    def check_compatibility(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Check compatibility between two versions"""
        if from_version not in self.versions:
            raise ValueError(f"Version {from_version} not found")
        
        if to_version not in self.versions:
            raise ValueError(f"Version {to_version} not found")
        
        from_ver = self.versions[from_version]
        to_ver = self.versions[to_version]
        
        # Check if to_version is backward compatible
        compatible = to_ver.backward_compatible
        
        # Find breaking changes
        breaking_changes = []
        for change in to_ver.changes:
            if change.change_type == ChangeType.BREAKING:
                breaking_changes.append(change)
        
        # Calculate migration complexity
        migration_complexity = "low"
        if breaking_changes:
            if len(breaking_changes) > 5:
                migration_complexity = "high"
            elif len(breaking_changes) > 2:
                migration_complexity = "medium"
        
        return {
            "compatible": compatible,
            "breaking_changes": len(breaking_changes),
            "migration_complexity": migration_complexity,
            "breaking_changes_details": [asdict(change) for change in breaking_changes],
            "migration_guide_available": bool(to_ver.migration_guide)
        }
    
    def generate_migration_plan(
        self,
        from_version: str,
        to_version: str,
        strategy: MigrationStrategy = MigrationStrategy.GRADUAL
    ) -> Dict[str, Any]:
        """Generate a migration plan between versions"""
        compatibility = self.check_compatibility(from_version, to_version)
        
        plan = {
            "from_version": from_version,
            "to_version": to_version,
            "strategy": strategy.value,
            "compatibility": compatibility,
            "steps": [],
            "estimated_duration": "unknown",
            "risk_level": "low"
        }
        
        if strategy == MigrationStrategy.IMMEDIATE:
            plan["steps"] = [
                "Update client code to use new version",
                "Test thoroughly in staging environment",
                "Deploy to production",
                "Monitor for issues"
            ]
            plan["estimated_duration"] = "1-2 days"
        
        elif strategy == MigrationStrategy.GRADUAL:
            plan["steps"] = [
                "Deploy new version alongside old version",
                "Migrate 10% of traffic to new version",
                "Monitor and fix issues",
                "Gradually increase traffic (25%, 50%, 75%, 100%)",
                "Deprecate old version after full migration"
            ]
            plan["estimated_duration"] = "1-2 weeks"
        
        elif strategy == MigrationStrategy.SCHEDULED:
            plan["steps"] = [
                "Announce migration schedule to users",
                "Provide migration tools and documentation",
                "Set deprecation date for old version",
                "Execute migration on scheduled date",
                "Monitor and support during transition"
            ]
            plan["estimated_duration"] = "2-4 weeks"
        
        # Adjust risk level based on breaking changes
        if compatibility["breaking_changes"] > 0:
            if compatibility["migration_complexity"] == "high":
                plan["risk_level"] = "high"
            elif compatibility["migration_complexity"] == "medium":
                plan["risk_level"] = "medium"
        
        return plan
    
    def execute_migration(
        self,
        from_version: str,
        to_version: str,
        strategy: MigrationStrategy,
        migration_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a migration between versions"""
        migration_id = str(uuid.uuid4())
        
        migration_record = {
            "migration_id": migration_id,
            "from_version": from_version,
            "to_version": to_version,
            "strategy": strategy.value,
            "start_time": datetime.now().isoformat(),
            "status": "in_progress",
            "migration_data": migration_data or {}
        }
        
        self.migration_history.append(migration_record)
        self._save_data()
        
        logger.info(f"Started migration {migration_id} from {from_version} to {to_version}")
        
        return migration_record
    
    def complete_migration(self, migration_id: str, success: bool = True, notes: str = ""):
        """Complete a migration"""
        for migration in self.migration_history:
            if migration["migration_id"] == migration_id:
                migration["end_time"] = datetime.now().isoformat()
                migration["status"] = "completed" if success else "failed"
                migration["notes"] = notes
                break
        
        self._save_data()
        
        logger.info(f"Completed migration {migration_id} with status: {'success' if success else 'failed'}")
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        return self.migration_history.copy()
    
    def create_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        deprecation_period_days: int = 90,
        sunset_period_days: int = 180,
        max_active_versions: int = 3,
        auto_deprecate: bool = True,
        require_migration_guide: bool = True,
        breaking_change_notice_days: int = 30
    ) -> VersionPolicy:
        """Create a new version policy"""
        if policy_id in self.policies:
            raise ValueError(f"Policy {policy_id} already exists")
        
        policy = VersionPolicy(
            policy_id=policy_id,
            name=name,
            description=description,
            deprecation_period_days=deprecation_period_days,
            sunset_period_days=sunset_period_days,
            max_active_versions=max_active_versions,
            auto_deprecate=auto_deprecate,
            require_migration_guide=require_migration_guide,
            breaking_change_notice_days=breaking_change_notice_days
        )
        
        self.policies[policy_id] = policy
        self._save_data()
        
        logger.info(f"Created version policy: {policy_id}")
        return policy
    
    def get_policy(self, policy_id: str) -> Optional[VersionPolicy]:
        """Get a version policy"""
        return self.policies.get(policy_id)
    
    def list_policies(self) -> List[VersionPolicy]:
        """List all version policies"""
        return list(self.policies.values())
    
    def get_version_summary(self) -> Dict[str, Any]:
        """Get summary of all versions"""
        summary = {
            "total_versions": len(self.versions),
            "by_status": defaultdict(int),
            "latest_version": None,
            "deprecated_versions": [],
            "sunset_versions": [],
            "breaking_changes_count": 0
        }
        
        for version in self.versions.values():
            summary["by_status"][version.status.value] += 1
            
            if version.status == VersionStatus.ACTIVE:
                if not summary["latest_version"] or semver.VersionInfo.parse(version.version) > semver.VersionInfo.parse(summary["latest_version"]):
                    summary["latest_version"] = version.version
            
            elif version.status == VersionStatus.DEPRECATED:
                summary["deprecated_versions"].append(version.version)
            
            elif version.status == VersionStatus.SUNSET:
                summary["sunset_versions"].append(version.version)
            
            # Count breaking changes
            for change in version.changes:
                if change.change_type == ChangeType.BREAKING:
                    summary["breaking_changes_count"] += 1
        
        return dict(summary)

# Import required modules
try:
    import semver
except ImportError:
    logger.warning("semver not available. Install with: pip install semver")
    # Fallback implementation
    class VersionInfo:
        def __init__(self, version_str):
            self.version_str = version_str
        
        @classmethod
        def parse(cls, version_str):
            return cls(version_str)
        
        def __gt__(self, other):
            return self.version_str > other.version_str
    
    semver.VersionInfo = VersionInfo

async def main():
    """Main function to demonstrate version manager"""
    data_dir = Path("./version_data")
    manager = VersionManager(data_dir)
    
    # Create a new version
    version = manager.create_version("1.0.0", "Initial API version")
    print(f"Created version: {version.version}")
    
    # Add some changes
    manager.add_change(
        "1.0.0",
        ChangeType.ADDITIVE,
        "Added new endpoint for user management",
        ["/users", "/users/{id}"]
    )
    
    # Release the version
    manager.release_version("1.0.0")
    print("Released version 1.0.0")
    
    # Create a new version with breaking changes
    version2 = manager.create_version("2.0.0", "Major API update", parent_version="1.0.0")
    manager.add_change(
        "2.0.0",
        ChangeType.BREAKING,
        "Changed user ID format from integer to UUID",
        ["/users/{id}"],
        breaking_changes=["User ID format change"],
        impact_level="high"
    )
    
    # Check compatibility
    compatibility = manager.check_compatibility("1.0.0", "2.0.0")
    print(f"Compatibility: {compatibility}")
    
    # Generate migration plan
    plan = manager.generate_migration_plan("1.0.0", "2.0.0", MigrationStrategy.GRADUAL)
    print(f"Migration plan: {plan}")
    
    # Get version summary
    summary = manager.get_version_summary()
    print(f"Version summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())