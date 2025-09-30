#!/usr/bin/env python3
"""
Setup Production Secrets Management System
Properly named script for setting up environment variables and secrets
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add workspace to path
sys.path.append(str(Path(__file__).parent))

from security.secrets_manager_simple import SimpleSecretsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to setup schema-driven secrets management"""
    logger.info("Setting up Schema-Driven Secrets Management System")
    
    # Get current directory as workspace path
    workspace_path = str(Path(__file__).parent)
    logger.info(f"Using workspace path: {workspace_path}")
    
    # Initialize secrets manager with correct path
    secrets_manager = SimpleSecretsManager(workspace_path)
    
    try:
        # Check if schema file exists
        schema_file = Path(workspace_path) / "configs" / "environment_schema.yaml"
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            logger.error("Please ensure configs/environment_schema.yaml exists")
            return False
        
        logger.info(f"Using schema file: {schema_file}")
        
        # Get available environments from schema
        if not secrets_manager.schema or 'environments' not in secrets_manager.schema:
            logger.error("No environments found in schema")
            return False
        
        available_environments = list(secrets_manager.schema['environments'].keys())
        logger.info(f"Available environments: {', '.join(available_environments)}")
        
        # Step 1: Generate secure secrets for all environments
        logger.info("Step 1: Generating secure secrets for all environments...")
        all_secrets = {}
        for env in available_environments:
            secrets_dict = await secrets_manager.generate_secure_secrets(env)
            all_secrets[env] = secrets_dict
            logger.info(f"Generated {len(secrets_dict)} secrets for {env}")
        
        # Step 2: Store secrets securely for each environment
        logger.info("Step 2: Storing secrets securely...")
        secrets_files = {}
        for env, secrets_dict in all_secrets.items():
            secrets_file = await secrets_manager.store_secrets(secrets_dict, env)
            secrets_files[env] = secrets_file
            logger.info(f"Secrets stored for {env}: {secrets_file}")
        
        # Step 3: Create environment files for all environments
        logger.info("Step 3: Creating environment files...")
        all_env_files = {}
        for env in available_environments:
            env_files = await secrets_manager.create_environment_files(env)
            all_env_files[env] = env_files
            logger.info(f"Created {len(env_files)} files for {env}:")
            for file in env_files:
                logger.info(f"  - {file}")
        
        # Step 4: Setup secret rotation
        logger.info("Step 4: Setting up secret rotation...")
        rotation_config = await secrets_manager.setup_secret_rotation()
        logger.info("Secret rotation configured")
        
        # Summary
        logger.info("=" * 60)
        logger.info("SCHEMA-DRIVEN SECRETS MANAGEMENT SETUP COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"✅ Generated secrets for {len(available_environments)} environments")
        logger.info("✅ Stored secrets securely")
        logger.info("✅ Created environment files")
        logger.info("✅ Set up secret rotation")
        logger.info("=" * 60)
        logger.info("Generated environments:")
        for env in available_environments:
            env_config = secrets_manager.schema['environments'][env]
            description = env_config.get('description', 'No description')
            gpu_required = env_config.get('gpu_required', False)
            memory_min = env_config.get('memory_min_gb', 'Unknown')
            logger.info(f"  - {env}: {description} (GPU: {'Yes' if gpu_required else 'No'}, Memory: {memory_min}GB)")
        logger.info("=" * 60)
        logger.info("Next steps:")
        logger.info("1. Review the generated .env.{environment} files")
        logger.info("2. Start your desired environment: ./start-environment.sh {environment}")
        logger.info("3. Test the services")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up secrets management: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
