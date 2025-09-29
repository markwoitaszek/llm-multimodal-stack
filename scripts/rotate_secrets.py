#!/usr/bin/env python3
"""
Automated Secret Rotation Script
"""
import asyncio
import sys
from pathlib import Path

# Add workspace to path
sys.path.append(str(Path(__file__).parent.parent))

from security.secrets_manager_simple import SimpleSecretsManager

async def main():
    """Main rotation function"""
    secrets_manager = SimpleSecretsManager()
    
    # Load current secrets
    current_secrets = await secrets_manager.load_secrets("production")
    
    # Generate new secrets
    new_secrets = await secrets_manager.generate_secure_secrets()
    
    # Backup current secrets
    backup_file = await secrets_manager.store_secrets(current_secrets, "backup")
    print(f"Backed up current secrets to {backup_file}")
    
    # Store new secrets
    new_file = await secrets_manager.store_secrets(new_secrets, "production")
    print(f"Stored new secrets to {new_file}")
    
    # Create new environment files
    await secrets_manager.create_environment_files("production")
    print("Created new environment files")
    
    print("Secret rotation completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
