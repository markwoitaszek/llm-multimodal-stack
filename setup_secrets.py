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
    """Main function to setup production secrets management"""
    logger.info("Setting up Production Secrets Management System")
    
    # Get current directory as workspace path
    workspace_path = str(Path(__file__).parent)
    logger.info(f"Using workspace path: {workspace_path}")
    
    # Initialize secrets manager with correct path
    secrets_manager = SimpleSecretsManager(workspace_path)
    
    try:
        # Step 1: Generate secure secrets
        logger.info("Step 1: Generating secure secrets...")
        secrets_dict = await secrets_manager.generate_secure_secrets()
        logger.info(f"Generated {len(secrets_dict)} secure secrets")
        
        # Step 2: Store secrets securely
        logger.info("Step 2: Storing secrets securely...")
        secrets_file = await secrets_manager.store_secrets(secrets_dict, "development")
        logger.info(f"Secrets stored in: {secrets_file}")
        
        # Step 3: Create environment files
        logger.info("Step 3: Creating environment files...")
        env_files = await secrets_manager.create_environment_files("development")
        logger.info(f"Created {len(env_files)} environment files:")
        for file in env_files:
            logger.info(f"  - {file}")
        
        # Step 4: Setup secret rotation
        logger.info("Step 4: Setting up secret rotation...")
        rotation_config = await secrets_manager.setup_secret_rotation()
        logger.info("Secret rotation configured")
        
        # Summary
        logger.info("=" * 60)
        logger.info("SECRETS MANAGEMENT SETUP COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("✅ Generated secure secrets")
        logger.info("✅ Stored secrets securely")
        logger.info("✅ Created environment files")
        logger.info("✅ Set up secret rotation")
        logger.info("=" * 60)
        logger.info("Next steps:")
        logger.info("1. Review the generated .env.development file")
        logger.info("2. Start your development environment")
        logger.info("3. Test the services")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up secrets management: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
