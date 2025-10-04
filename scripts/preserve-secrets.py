#!/usr/bin/env python3
"""
Preserve Secrets Script - Prevents credential regeneration on restart
This script checks if secrets already exist and only generates new ones if needed.
"""
import asyncio
import sys
import logging
import json
from pathlib import Path

# Add workspace to path
sys.path.append(str(Path(__file__).parent.parent))

from security.secrets_manager_simple import SimpleSecretsManager
from setup_secrets import TemplateBasedSecretsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PreservingSecretsManager(TemplateBasedSecretsManager):
    """Secrets manager that preserves existing credentials"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        super().__init__(workspace_path)
        self.force_regenerate = False
    
    async def setup_secrets_with_preservation(self, environment: str = "development", force: bool = False) -> bool:
        """Setup secrets, preserving existing ones unless forced"""
        logger.info(f"Setting up secrets for {environment} (preserve existing: {not force})")
        
        self.force_regenerate = force
        
        try:
            # Check if secrets already exist
            secrets_file = self.secrets_dir / f".env.{environment}.json"
            env_file = self.workspace_path / f".env.{environment}"
            
            if not force and secrets_file.exists() and env_file.exists():
                logger.info(f"✅ Secrets already exist for {environment}")
                logger.info(f"   Secrets file: {secrets_file}")
                logger.info(f"   Env file: {env_file}")
                
                # Validate existing secrets
                try:
                    secrets_dict = await self.load_secrets(environment)
                    logger.info(f"✅ Loaded {len(secrets_dict)} existing secrets")
                    
                    # Copy to .env for Docker Compose
                    if env_file.exists():
                        import shutil
                        shutil.copy2(env_file, self.workspace_path / ".env")
                        logger.info("✅ Copied existing .env.{environment} to .env")
                    
                    return True
                    
                except Exception as e:
                    logger.warning(f"⚠️  Existing secrets validation failed: {e}")
                    logger.info("🔄 Proceeding with secret regeneration...")
            
            # Generate new secrets
            logger.info("🔄 Generating new secrets...")
            secrets_dict = await self.generate_secure_secrets()
            logger.info(f"Generated {len(secrets_dict)} secure secrets")
            
            # Store secrets securely
            logger.info("💾 Storing secrets securely...")
            secrets_file = await self.store_secrets(secrets_dict, environment)
            logger.info(f"Secrets stored in: {secrets_file}")
            
            # Create legacy .env file for backward compatibility
            logger.info("📝 Creating legacy .env file...")
            legacy_env_file = await self.create_legacy_env_file(environment)
            logger.info(f"Created legacy .env file: {legacy_env_file}")
            
            # Copy to .env for Docker Compose
            import shutil
            shutil.copy2(legacy_env_file, self.workspace_path / ".env")
            logger.info("✅ Copied .env.{environment} to .env")
            
            logger.info("✅ Secrets setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up secrets: {e}")
            return False

async def main():
    """Main function"""
    import argparse
    parser = argparse.ArgumentParser(description='Setup secrets with preservation')
    parser.add_argument(
        '--environment', '-e',
        default='development',
        choices=['development', 'staging', 'production'],
        help='Environment to setup secrets for (default: development)'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force regeneration of secrets even if they exist'
    )
    args = parser.parse_args()
    
    # Get current directory as workspace path
    workspace_path = str(Path(__file__).parent.parent)
    logger.info(f"Using workspace path: {workspace_path}")
    
    # Initialize the preserving secrets manager
    secrets_manager = PreservingSecretsManager(workspace_path)
    
    success = await secrets_manager.setup_secrets_with_preservation(args.environment, args.force)
    
    if success:
        logger.info("🎉 Secrets setup completed successfully!")
        if not args.force:
            logger.info("💡 Use --force to regenerate secrets even if they exist")
    else:
        logger.error("❌ Secrets setup failed!")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
