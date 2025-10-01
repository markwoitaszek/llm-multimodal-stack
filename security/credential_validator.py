#!/usr/bin/env python3
"""
Credential Validation Module
Validates credentials before deployment to prevent authentication failures
"""
import argparse
import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml

try:
    from jinja2 import Environment, FileSystemLoader, TemplateError, UndefinedError
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of credential validation"""
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)
        self.passed = False
    
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another result into this one"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.details.update(other.details)
        if not other.passed:
            self.passed = False
    
    def __str__(self) -> str:
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        output = [f"\nValidation Result: {status}"]
        
        if self.errors:
            output.append(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                output.append(f"  • {error}")
        
        if self.warnings:
            output.append(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                output.append(f"  • {warning}")
        
        return "\n".join(output)


class CredentialValidator:
    """Validates credentials before deployment"""
    
    # Password complexity requirements
    PASSWORD_POLICY = {
        'min_length': 16,
        'max_length': 128,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special': True,
        # Characters that cause issues in shell, Docker, or URLs
        'forbidden_chars': ['$', '{', '}', '`', '\\', '<', '>', '[', ']'],
        'forbidden_patterns': [
            (r'(.)\1{3,}', 'No more than 3 repeated characters'),
            (r'(123|abc|qwerty)', 'No common sequences'),
            (r'(password|admin|secret)', 'No common words'),
        ]
    }
    
    # API key requirements
    API_KEY_POLICY = {
        'min_length': 32,
        'max_length': 128,
    }
    
    # Forbidden placeholder values
    FORBIDDEN_PLACEHOLDERS = [
        'changeme', 'change-me', 'changeme_in_production',
        'placeholder', 'placeholder-change-me',
        'postgres', 'minioadmin', 'admin',
        'password', 'secret', 'test', 'dummy',
        'your-secret', 'your-password'
    ]
    
    # Required secrets by category
    REQUIRED_SECRETS = {
        'database': ['POSTGRES_PASSWORD'],
        'storage': ['MINIO_ROOT_PASSWORD'],
        'api': ['LITELLM_MASTER_KEY', 'LITELLM_SALT_KEY', 'VLLM_API_KEY'],
        'auth': ['JWT_SECRET_KEY', 'WEBUI_SECRET_KEY'],
        'n8n': ['N8N_PASSWORD', 'N8N_ENCRYPTION_KEY']
    }
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
        self.secrets_dir = self.workspace_path / "secrets"
        self.templates_dir = self.workspace_path / "env-templates"
        self.env_d_dir = self.workspace_path / ".env.d"
        
    def validate_all(self, environment: str, strict: bool = False) -> ValidationResult:
        """Run all validation checks"""
        logger.info(f"Running comprehensive validation for {environment} environment")
        
        result = ValidationResult()
        result.details['environment'] = environment
        result.details['strict_mode'] = strict
        
        # 1. Check files exist
        logger.info("Step 1/6: Checking files exist...")
        file_check = self.check_files_exist(environment)
        result.merge(file_check)
        if not file_check.passed and strict:
            return result
        
        # 2. Validate credential strength
        logger.info("Step 2/6: Validating credential strength...")
        strength_check = self.validate_strength(environment)
        result.merge(strength_check)
        
        # 3. Check for placeholders
        logger.info("Step 3/6: Checking for placeholder values...")
        placeholder_check = self.check_placeholders(environment, strict)
        result.merge(placeholder_check)
        
        # 4. Validate consistency
        logger.info("Step 4/6: Validating consistency across files...")
        consistency_check = self.validate_consistency(environment)
        result.merge(consistency_check)
        
        # 5. Validate templates
        logger.info("Step 5/6: Validating Jinja2 templates...")
        template_check = self.validate_templates(environment)
        result.merge(template_check)
        
        # 6. Validate required secrets present
        logger.info("Step 6/6: Checking required secrets are present...")
        required_check = self.check_required_secrets(environment)
        result.merge(required_check)
        
        logger.info(f"Validation complete: {'PASSED' if result.passed else 'FAILED'}")
        return result
    
    def check_files_exist(self, environment: str) -> ValidationResult:
        """Check that required credential files exist"""
        result = ValidationResult()
        
        required_files = [
            (self.secrets_dir / f".env.{environment}.json", "Secrets JSON file"),
            (self.workspace_path / f".env.{environment}", "Environment file"),
        ]
        
        for file_path, description in required_files:
            if not file_path.exists():
                result.add_error(f"{description} not found: {file_path}")
            else:
                logger.debug(f"✓ Found {description}: {file_path}")
        
        result.details['files_checked'] = len(required_files)
        return result
    
    def validate_strength(self, environment: str) -> ValidationResult:
        """Validate credential strength"""
        result = ValidationResult()
        
        # Load secrets
        secrets_file = self.secrets_dir / f".env.{environment}.json"
        if not secrets_file.exists():
            result.add_error(f"Secrets file not found: {secrets_file}")
            return result
        
        with open(secrets_file, 'r') as f:
            secrets = json.load(f)
        
        result.details['total_secrets'] = len(secrets)
        result.details['validated_secrets'] = 0
        result.details['weak_secrets'] = []
        
        for key, value in secrets.items():
            # Skip placeholder external API keys
            if key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']:
                continue
            
            # Validate passwords
            if 'PASSWORD' in key or 'SECRET' in key:
                validation = self._validate_password_strength(key, value)
                if not validation[0]:
                    result.add_warning(f"{key}: {validation[1]}")
                    result.details['weak_secrets'].append(key)
                else:
                    result.details['validated_secrets'] += 1
            
            # Validate API keys
            elif 'API_KEY' in key or 'KEY' in key:
                validation = self._validate_api_key_strength(key, value)
                if not validation[0]:
                    result.add_warning(f"{key}: {validation[1]}")
                    result.details['weak_secrets'].append(key)
                else:
                    result.details['validated_secrets'] += 1
        
        return result
    
    def _validate_password_strength(self, key: str, password: str) -> Tuple[bool, str]:
        """Validate password meets strength requirements"""
        policy = self.PASSWORD_POLICY
        
        # Check length
        if len(password) < policy['min_length']:
            return False, f"Too short (minimum {policy['min_length']} characters)"
        
        if len(password) > policy['max_length']:
            return False, f"Too long (maximum {policy['max_length']} characters)"
        
        # Check character requirements
        if policy['require_uppercase'] and not any(c.isupper() for c in password):
            return False, "Missing uppercase letters"
        
        if policy['require_lowercase'] and not any(c.islower() for c in password):
            return False, "Missing lowercase letters"
        
        if policy['require_digits'] and not any(c.isdigit() for c in password):
            return False, "Missing digits"
        
        if policy['require_special']:
            special_chars = "!%^*()_+-"
            if not any(c in special_chars for c in password):
                return False, "Missing special characters"
        
        # Check for forbidden characters
        for char in policy['forbidden_chars']:
            if char in password:
                return False, f"Contains forbidden character: {char}"
        
        # Check for forbidden patterns
        for pattern, description in policy['forbidden_patterns']:
            if re.search(pattern, password, re.IGNORECASE):
                return False, f"Contains forbidden pattern: {description}"
        
        return True, "Valid"
    
    def _validate_api_key_strength(self, key: str, api_key: str) -> Tuple[bool, str]:
        """Validate API key meets strength requirements"""
        policy = self.API_KEY_POLICY
        
        # Check length
        if len(api_key) < policy['min_length']:
            return False, f"Too short (minimum {policy['min_length']} characters)"
        
        if len(api_key) > policy['max_length']:
            return False, f"Too long (maximum {policy['max_length']} characters)"
        
        return True, "Valid"
    
    def check_placeholders(self, environment: str, strict: bool = False) -> ValidationResult:
        """Check for placeholder values"""
        result = ValidationResult()
        
        # External API keys that can be placeholders in non-production
        EXTERNAL_API_KEYS = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
        
        # Load secrets
        secrets_file = self.secrets_dir / f".env.{environment}.json"
        if not secrets_file.exists():
            return result
        
        with open(secrets_file, 'r') as f:
            secrets = json.load(f)
        
        placeholders_found = []
        
        for key, value in secrets.items():
            value_lower = value.lower()
            for placeholder in self.FORBIDDEN_PLACEHOLDERS:
                if placeholder in value_lower:
                    placeholders_found.append((key, value))
                    break
        
        if placeholders_found:
            if environment in ['production', 'staging'] or strict:
                for key, value in placeholders_found:
                    # Allow external API key placeholders in staging (warn only)
                    if environment == 'staging' and key in EXTERNAL_API_KEYS:
                        result.add_warning(f"{key} contains placeholder value (optional service)")
                    else:
                        result.add_error(f"{key} contains placeholder value: {value[:20]}...")
            else:
                for key, value in placeholders_found:
                    result.add_warning(f"{key} contains placeholder value (OK for dev)")
        
        result.details['placeholders_found'] = len(placeholders_found)
        return result
    
    def validate_consistency(self, environment: str) -> ValidationResult:
        """Validate consistency between secrets and environment files"""
        result = ValidationResult()
        
        # Load secrets JSON
        secrets_file = self.secrets_dir / f".env.{environment}.json"
        env_file = self.workspace_path / f".env.{environment}"
        
        if not secrets_file.exists() or not env_file.exists():
            return result
        
        with open(secrets_file, 'r') as f:
            secrets_json = json.load(f)
        
        # Parse .env file
        env_vars = self._parse_env_file(env_file)
        
        # Check that secrets match
        inconsistencies = []
        for key in secrets_json:
            if key in env_vars:
                if secrets_json[key] != env_vars[key]:
                    inconsistencies.append(key)
                    result.add_error(
                        f"{key}: Value in .env.{environment} doesn't match secrets JSON"
                    )
        
        result.details['inconsistencies'] = len(inconsistencies)
        return result
    
    def _parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """Parse a .env file into a dictionary"""
        env_vars = {}
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        return env_vars
    
    def validate_templates(self, environment: str) -> ValidationResult:
        """Validate that all Jinja2 templates render correctly"""
        result = ValidationResult()
        
        if not JINJA2_AVAILABLE:
            result.add_warning("Jinja2 not available, skipping template validation")
            return result
        
        if not self.templates_dir.exists():
            result.add_error(f"Templates directory not found: {self.templates_dir}")
            return result
        
        # Load secrets for rendering
        secrets_file = self.secrets_dir / f".env.{environment}.json"
        if not secrets_file.exists():
            return result
        
        with open(secrets_file, 'r') as f:
            secrets = json.load(f)
        
        # Convert secrets to template variables
        template_vars = {}
        for key, value in secrets.items():
            template_vars[f"vault_{key.lower()}"] = value
        
        # Add default variables
        template_vars.update({
            'environment': environment,
            'debug': environment == 'development',
            'log_level': 'DEBUG' if environment == 'development' else 'INFO'
        })
        
        # Initialize Jinja2 environment
        try:
            jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=False
            )
        except Exception as e:
            result.add_error(f"Failed to initialize Jinja2 environment: {e}")
            return result
        
        # Find all template files
        template_files = list(self.templates_dir.glob("*.j2"))
        result.details['total_templates'] = len(template_files)
        result.details['valid_templates'] = 0
        result.details['invalid_templates'] = []
        
        for template_file in template_files:
            try:
                template = jinja_env.get_template(template_file.name)
                rendered = template.render(**template_vars)
                result.details['valid_templates'] += 1
                logger.debug(f"✓ Template renders correctly: {template_file.name}")
            except UndefinedError as e:
                result.add_error(f"{template_file.name}: Undefined variable - {e}")
                result.details['invalid_templates'].append(template_file.name)
            except TemplateError as e:
                result.add_error(f"{template_file.name}: Template error - {e}")
                result.details['invalid_templates'].append(template_file.name)
            except Exception as e:
                result.add_error(f"{template_file.name}: Unexpected error - {e}")
                result.details['invalid_templates'].append(template_file.name)
        
        return result
    
    def check_required_secrets(self, environment: str) -> ValidationResult:
        """Check that all required secrets are present"""
        result = ValidationResult()
        
        # Load secrets
        secrets_file = self.secrets_dir / f".env.{environment}.json"
        if not secrets_file.exists():
            return result
        
        with open(secrets_file, 'r') as f:
            secrets = json.load(f)
        
        missing_secrets = []
        
        for category, required_keys in self.REQUIRED_SECRETS.items():
            for key in required_keys:
                if key not in secrets:
                    missing_secrets.append((category, key))
                    result.add_error(f"Missing required secret ({category}): {key}")
        
        result.details['missing_secrets'] = len(missing_secrets)
        result.details['required_secrets'] = sum(
            len(keys) for keys in self.REQUIRED_SECRETS.values()
        )
        
        return result
    
    async def test_connections(self, environment: str, timeout: int = 10) -> ValidationResult:
        """Test that services can connect with generated credentials"""
        result = ValidationResult()
        result.add_warning("Connection testing not yet implemented")
        # TODO: Implement actual connection tests
        # - PostgreSQL: psycopg2/asyncpg
        # - Redis: redis-py
        # - MinIO: boto3
        return result


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Validate credentials before deployment'
    )
    parser.add_argument(
        'command',
        choices=['validate', 'strength', 'templates', 'placeholders', 'consistency'],
        help='Validation command to run'
    )
    parser.add_argument(
        '--environment', '-e',
        default='development',
        help='Environment to validate (default: development)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict mode (fail on warnings)'
    )
    parser.add_argument(
        '--workspace', '-w',
        default='.',
        help='Workspace path (default: current directory)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    validator = CredentialValidator(workspace_path=args.workspace)
    
    # Run requested validation
    if args.command == 'validate':
        result = validator.validate_all(args.environment, args.strict)
    elif args.command == 'strength':
        result = validator.validate_strength(args.environment)
    elif args.command == 'templates':
        result = validator.validate_templates(args.environment)
    elif args.command == 'placeholders':
        result = validator.check_placeholders(args.environment, args.strict)
    elif args.command == 'consistency':
        result = validator.validate_consistency(args.environment)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)
    
    # Output results
    if args.json:
        output = {
            'passed': result.passed,
            'errors': result.errors,
            'warnings': result.warnings,
            'details': result.details
        }
        print(json.dumps(output, indent=2))
    else:
        print(result)
    
    # Exit with appropriate code
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()

