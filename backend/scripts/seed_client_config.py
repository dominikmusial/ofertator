#!/usr/bin/env python3
"""
Seed script for client-specific configuration.
Configures feature flags and creates admin account.

Usage:
    python backend/scripts/seed_client_config.py \\
        --marketplace-enabled allegro=false \\
        --marketplace-enabled decathlon=true \\
        --marketplace-enabled castorama=true \\
        --marketplace-enabled leroymerlin=true \\
        --feature registration=false \\
        --feature google_sso=false \\
        --create-admin admin@client.com password123

Or set environment variables:
    CLIENT_ADMIN_EMAIL=admin@client.com \\
    CLIENT_ADMIN_PASSWORD=secure_password \\
    python backend/scripts/seed_client_config.py --client-mode
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.repositories import SystemConfigRepository, AdminRepository
from app.db import models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Seed client-specific configuration'
    )
    
    parser.add_argument(
        '--marketplace-enabled',
        action='append',
        dest='marketplaces',
        help='Marketplace enable/disable (format: name=true/false)'
    )
    
    parser.add_argument(
        '--feature',
        action='append',
        dest='features',
        help='Feature enable/disable (format: name=true/false)'
    )
    
    parser.add_argument(
        '--create-admin',
        nargs=2,
        metavar=('EMAIL', 'PASSWORD'),
        help='Create admin account with email and password'
    )
    
    parser.add_argument(
        '--client-mode',
        action='store_true',
        help='Use client mode with env vars (disables Allegro, registration, Google SSO)'
    )
    
    return parser.parse_args()


def update_marketplace_flag(db, marketplace: str, enabled: bool, admin_user_id: int = 1):
    """Update marketplace feature flag"""
    key = f"feature.marketplace.{marketplace.lower()}.enabled"
    value = "true" if enabled else "false"
    
    SystemConfigRepository.update(
        db=db,
        config_key=key,
        config_value=value,
        user_id=admin_user_id,
        description=f"Enable/disable {marketplace} marketplace"
    )
    logger.info(f"✓ Set {marketplace} marketplace: {value}")


def update_auth_flag(db, feature: str, enabled: bool, admin_user_id: int = 1):
    """Update auth feature flag"""
    key = f"feature.auth.{feature.lower()}.enabled"
    value = "true" if enabled else "false"
    
    SystemConfigRepository.update(
        db=db,
        config_key=key,
        config_value=value,
        user_id=admin_user_id,
        description=f"Enable/disable {feature}"
    )
    logger.info(f"✓ Set auth.{feature}: {value}")


def update_admin_flag(db, feature: str, enabled: bool, admin_user_id: int = 1):
    """Update admin feature flag"""
    key = f"feature.admin.{feature.lower()}.enabled"
    value = "true" if enabled else "false"
    
    SystemConfigRepository.update(
        db=db,
        config_key=key,
        config_value=value,
        user_id=admin_user_id,
        description=f"Enable/disable {feature} admin feature"
    )
    logger.info(f"✓ Set admin.{feature}: {value}")


def update_module_flag(db, module: str, enabled: bool, admin_user_id: int = 1):
    """Update module feature flag"""
    key = f"feature.modules.{module.lower()}.enabled"
    value = "true" if enabled else "false"
    
    SystemConfigRepository.update(
        db=db,
        config_key=key,
        config_value=value,
        user_id=admin_user_id,
        description=f"Enable/disable {module} module"
    )
    logger.info(f"✓ Set modules.{module}: {value}")


def update_user_flag(db, feature: str, enabled: bool, admin_user_id: int = 1):
    """Update user feature flag"""
    key = f"feature.user.{feature.lower()}.enabled"
    value = "true" if enabled else "false"
    
    SystemConfigRepository.update(
        db=db,
        config_key=key,
        config_value=value,
        user_id=admin_user_id,
        description=f"Enable/disable {feature} user feature"
    )
    logger.info(f"✓ Set user.{feature}: {value}")


def main():
    args = parse_args()
    db = SessionLocal()
    
    try:
        logger.info("Starting client configuration seed...")
        
        # Client mode: preset configuration
        if args.client_mode:
            logger.info("\n=== CLIENT MODE CONFIGURATION ===")
            
            # Create admin from env vars FIRST (so user ID 1 exists for feature flag updates)
            admin_email = os.getenv('CLIENT_ADMIN_EMAIL')
            admin_password = os.getenv('CLIENT_ADMIN_PASSWORD')
            
            if admin_email and admin_password:
                logger.info(f"\nCreating admin account: {admin_email}")
                admin = AdminRepository.create_default_admin(
                    db=db,
                    email=admin_email,
                    password=admin_password
                )
                logger.info(f"✓ Admin account created/verified: {admin.email}")
            else:
                logger.warning("⚠ CLIENT_ADMIN_EMAIL and CLIENT_ADMIN_PASSWORD not set")
            
            # Now update feature flags (admin user ID 1 exists now)
            # Disable Allegro
            update_marketplace_flag(db, "allegro", False)
            
            # Enable Mirakl marketplaces
            update_marketplace_flag(db, "decathlon", True)
            update_marketplace_flag(db, "castorama", True)
            update_marketplace_flag(db, "leroymerlin", True)
            
            # Disable public registration and Google SSO
            update_auth_flag(db, "registration", False)
            update_auth_flag(db, "google_sso", False)
            
            # Disable admin features (except user management)
            update_admin_flag(db, "ai_config", False)
            update_admin_flag(db, "team_analytics", False)
            
            # Disable modules
            update_module_flag(db, "ai_usage", False)
            
            # Disable user AI configuration (use env Gemini key only)
            update_user_flag(db, "ai_config", False)
        
        # Custom configuration
        else:
            # Process marketplace flags
            if args.marketplaces:
                logger.info("\n=== MARKETPLACE CONFIGURATION ===")
                for marketplace_setting in args.marketplaces:
                    try:
                        name, value = marketplace_setting.split('=')
                        enabled = value.lower() in ('true', '1', 'yes', 'enabled')
                        update_marketplace_flag(db, name, enabled)
                    except ValueError:
                        logger.error(f"✗ Invalid format: {marketplace_setting}")
            
            # Process feature flags
            if args.features:
                logger.info("\n=== FEATURE CONFIGURATION ===")
                for feature_setting in args.features:
                    try:
                        name, value = feature_setting.split('=')
                        enabled = value.lower() in ('true', '1', 'yes', 'enabled')
                        update_auth_flag(db, name, enabled)
                    except ValueError:
                        logger.error(f"✗ Invalid format: {feature_setting}")
            
            # Create admin account
            if args.create_admin:
                email, password = args.create_admin
                logger.info(f"\n=== ADMIN ACCOUNT ===")
                logger.info(f"Creating admin account: {email}")
                admin = AdminRepository.create_default_admin(
                    db=db,
                    email=email,
                    password=password
                )
                logger.info(f"✓ Admin account created/verified: {admin.email}")
        
        logger.info("\n✓ Client configuration seed completed successfully!")
        
    except Exception as e:
        logger.error(f"✗ Error during seed: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
