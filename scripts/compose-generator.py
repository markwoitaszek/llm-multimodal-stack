#!/usr/bin/env python3
"""
Compose Generator - Unified Schema to Docker Compose Files
Generates all Docker Compose files from a single unified schema
"""
import yaml
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

class ComposeGenerator:
    """Generates Docker Compose files from unified schema"""
    
    def __init__(self, schema_path: str = "schemas/compose-schema.yaml"):
        self.schema_path = Path(schema_path)
        self.output_dir = Path(".")
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the unified schema"""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
            
        with open(self.schema_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _expand_healthcheck(self, service: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Expand healthcheck template"""
        if 'healthcheck' not in service:
            return None
            
        hc = service['healthcheck']
        if 'template' in hc:
            template_name = hc['template']
            if template_name in self.schema['config']['health_checks']:
                template = self.schema['config']['health_checks'][template_name]
                # Merge template with service-specific settings
                expanded = template.copy()
                expanded.update({k: v for k, v in hc.items() if k != 'template'})
                return expanded
        return hc
    
    def _expand_service(self, service_name: str, service_def: Dict[str, Any], environment: str = None) -> Dict[str, Any]:
        """Expand a service definition with environment-specific overrides"""
        service = service_def.copy()
        
        # Apply environment overrides if specified
        if environment and environment in self.schema.get('environments', {}):
            env_config = self.schema['environments'][environment]
            if 'overrides' in env_config:
                overrides = env_config['overrides']
                
                # Apply service-specific overrides
                if service_name in overrides:
                    service.update(overrides[service_name])
                
                # Apply global overrides
                for key, value in overrides.items():
                    if key not in ['replicas', 'resources'] and key not in self.schema['services']:
                        service[key] = value
        
        # Expand healthcheck template
        if 'healthcheck' in service:
            service['healthcheck'] = self._expand_healthcheck(service)
        
        # Add restart policy
        if 'restart' not in service:
            service['restart'] = self.schema['config']['default_restart_policy']
        
        # Add networks
        if 'networks' not in service:
            service['networks'] = [self.schema['config']['network_name']]
        
        # Remove metadata fields that shouldn't be in final compose file
        metadata_fields = ['category', 'volumes_required', 'profiles', 'debug', 'log_level']
        for field in metadata_fields:
            if field in service:
                del service[field]
        
        return service
    
    def _get_volumes_for_services(self, services: List[str]) -> Dict[str, Dict[str, str]]:
        """Get volume definitions for a list of services"""
        volumes = {}
        
        for service_name in services:
            if service_name in self.schema['services']:
                service = self.schema['services'][service_name]
                if 'volumes_required' in service:
                    for volume_name in service['volumes_required']:
                        if volume_name in self.schema.get('volumes', {}):
                            volumes[volume_name] = self.schema['volumes'][volume_name]
        
        return volumes
    
    def _get_services_for_environment(self, environment: str) -> List[str]:
        """Get list of services for a specific environment"""
        if environment not in self.schema.get('environments', {}):
            raise ValueError(f"Environment '{environment}' not found in schema")
        
        return self.schema['environments'][environment]['services']
    
    def _apply_profiles(self, services: Dict[str, Dict[str, Any]], environment: str) -> Dict[str, Dict[str, Any]]:
        """Apply Docker profiles to services"""
        profiled_services = {}
        
        for service_name, service_def in services.items():
            service = service_def.copy()
            
            # Add profiles if the service has them
            if 'profiles' in service:
                # Only include services that match environment profiles
                if environment == 'development':
                    # Development includes core services only
                    if service_def.get('category') in ['core', 'inference', 'multimodal']:
                        if 'profiles' in service:
                            del service['profiles']
                        profiled_services[service_name] = service
                elif environment in ['staging', 'production']:
                    # Staging and production include all services
                    if 'profiles' in service:
                        del service['profiles']
                    profiled_services[service_name] = service
                else:
                    # Other environments use profiles
                    profiled_services[service_name] = service
            else:
                profiled_services[service_name] = service
        
        return profiled_services
    
    def generate_base_compose(self) -> str:
        """Generate base compose.yml with core services"""
        core_services = ['postgres', 'redis', 'qdrant', 'minio', 'vllm', 'litellm', 'multimodal-worker', 'retrieval-proxy']
        
        services = {}
        for service_name in core_services:
            if service_name in self.schema['services']:
                services[service_name] = self._expand_service(service_name, self.schema['services'][service_name])
        
        # Get volumes for core services
        volumes = self._get_volumes_for_services(core_services)
        
        compose = {
            'services': services,
            'volumes': volumes,
            'networks': {
                self.schema['config']['network_name']: self.schema['config']['network']
            }
        }
        
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def generate_override_compose(self, environment: str) -> str:
        """Generate environment-specific override compose file"""
        if environment not in self.schema.get('environments', {}):
            raise ValueError(f"Environment '{environment}' not found in schema")
        
        env_config = self.schema['environments'][environment]
        services = {}
        
        for service_name in env_config['services']:
            if service_name in self.schema['services']:
                services[service_name] = self._expand_service(service_name, self.schema['services'][service_name], environment)
        
        # Apply profiles
        services = self._apply_profiles(services, environment)
        
        # Get volumes for environment services
        volumes = self._get_volumes_for_services(env_config['services'])
        
        compose = {
            'services': services,
            'volumes': volumes
        }
        
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def generate_profile_compose(self, profile: str) -> str:
        """Generate compose file for a specific profile"""
        profile_services = {}
        profile_volumes = {}
        
        for service_name, service_def in self.schema['services'].items():
            if 'profiles' in service_def and profile in service_def['profiles']:
                profile_services[service_name] = self._expand_service(service_name, service_def)
                if 'volumes_required' in service_def:
                    for volume_name in service_def['volumes_required']:
                        if volume_name in self.schema.get('volumes', {}):
                            profile_volumes[volume_name] = self.schema['volumes'][volume_name]
        
        compose = {
            'services': profile_services,
            'volumes': profile_volumes
        }
        
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def generate_all_compose_files(self):
        """Generate all compose files from the schema"""
        print("Generating Docker Compose files from unified schema...")
        
        # Generate base compose.yml
        base_content = self.generate_base_compose()
        with open(self.output_dir / "compose.yml", 'w') as f:
            f.write(base_content)
        print("✅ Generated compose.yml")
        
        # Generate environment-specific overrides
        environments = ['development', 'staging', 'production', 'gpu', 'monitoring']
        for env in environments:
            if env in self.schema.get('environments', {}):
                try:
                    content = self.generate_override_compose(env)
                    filename = f"compose.{env}.yml"
                    with open(self.output_dir / filename, 'w') as f:
                        f.write(content)
                    print(f"✅ Generated {filename}")
                except Exception as e:
                    print(f"❌ Failed to generate compose.{env}.yml: {e}")
        
        # Generate profile-specific compose files
        profiles = ['services', 'monitoring', 'elk', 'logging', 'n8n-monitoring']
        for profile in profiles:
            content = self.generate_profile_compose(profile)
            if content.strip():  # Only write if there are services
                filename = f"compose.{profile}.yml"
                with open(self.output_dir / filename, 'w') as f:
                    f.write(content)
                print(f"✅ Generated {filename}")
        
        print(f"\n🎉 Generated {len(list(self.output_dir.glob('compose*.yml')))} compose files from unified schema")
    
    def validate_schema(self) -> List[str]:
        """Validate the schema for common issues"""
        errors = []
        
        # Check required top-level keys
        # Note: 'version' is no longer required (obsolete in Docker Compose v2)
        required_keys = ['config', 'services', 'environments']
        for key in required_keys:
            if key not in self.schema:
                errors.append(f"Missing required key: {key}")
        
        # Check service definitions
        if 'services' in self.schema:
            for service_name, service_def in self.schema['services'].items():
                if not isinstance(service_def, dict):
                    errors.append(f"Service '{service_name}' must be a dictionary")
                    continue
                
                # Check for required service fields
                if 'image' not in service_def and 'build' not in service_def:
                    errors.append(f"Service '{service_name}' must have 'image' or 'build'")
                
                # Check dependencies
                if 'depends_on' in service_def:
                    for dep in service_def['depends_on']:
                        if dep not in self.schema['services']:
                            errors.append(f"Service '{service_name}' depends on unknown service '{dep}'")
        
        # Check environment definitions
        if 'environments' in self.schema:
            for env_name, env_def in self.schema['environments'].items():
                if not isinstance(env_def, dict):
                    errors.append(f"Environment '{env_name}' must be a dictionary")
                    continue
                
                if 'services' not in env_def:
                    errors.append(f"Environment '{env_name}' must have 'services' list")
                else:
                    for service_name in env_def['services']:
                        if service_name not in self.schema['services']:
                            errors.append(f"Environment '{env_name}' references unknown service '{service_name}'")
        
        return errors

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Docker Compose files from unified schema')
    parser.add_argument('--schema', default='schemas/compose-schema.yaml', help='Path to schema file')
    parser.add_argument('--validate-only', action='store_true', help='Only validate schema, do not generate files')
    parser.add_argument('--output-dir', default='.', help='Output directory for generated files')
    parser.add_argument('--environment', help='Generate files for specific environment only')
    parser.add_argument('--profile', help='Generate files for specific profile only')
    
    args = parser.parse_args()
    
    try:
        generator = ComposeGenerator(args.schema)
        generator.output_dir = Path(args.output_dir)
        
        # Validate schema
        print("Validating schema...")
        errors = generator.validate_schema()
        if errors:
            print("❌ Schema validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("✅ Schema validation passed")
        
        if args.validate_only:
            return
        
        # Generate files
        if args.environment:
            content = generator.generate_override_compose(args.environment)
            filename = f"compose.{args.environment}.yml"
            with open(generator.output_dir / filename, 'w') as f:
                f.write(content)
            print(f"✅ Generated {filename}")
        elif args.profile:
            content = generator.generate_profile_compose(args.profile)
            filename = f"compose.{args.profile}.yml"
            with open(generator.output_dir / filename, 'w') as f:
                f.write(content)
            print(f"✅ Generated {filename}")
        else:
            generator.generate_all_compose_files()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()