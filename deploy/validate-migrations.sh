#!/bin/bash

# Migration Validation Script for Bot-sok
# Prevents migration conflicts and ensures safe deployments

set -e  # Exit on any error

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
DB_USER="${DB_USER:-user}"
DB_NAME="${DB_NAME:-allegro_bot_prod}"

echo "🔍 Starting migration validation..."

# Function to check if database is accessible
check_db_connection() {
    echo "📡 Checking database connection..."
    if ! docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -c '\l' >/dev/null 2>&1; then
        echo "❌ Cannot connect to database"
        return 1
    fi
    echo "✅ Database connection OK"
}

# Function to check for migration conflicts
check_migration_conflicts() {
    echo "🔍 Checking for migration conflicts..."
    
    # Count entries in alembic_version table
    HEAD_COUNT=$(docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM alembic_version;" 2>/dev/null | tr -d ' \t\n\r' || echo "0")
    
    echo "Migration heads in database: $HEAD_COUNT"
    
    if [ "$HEAD_COUNT" -gt 1 ]; then
        echo "❌ MIGRATION CONFLICT: Multiple heads detected"
        echo "Current heads in database:"
        docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT version_num FROM alembic_version ORDER BY version_num;"
        return 1
    elif [ "$HEAD_COUNT" -eq 0 ]; then
        echo "⚠️  No migration head found - database might be uninitialized"
        return 1
    fi
    
    echo "✅ No migration conflicts detected"
    return 0
}

# Function to get current migration status
get_migration_status() {
    echo "📋 Getting current migration status..."
    
    # Check if backend service is available
    echo "🔍 Checking if backend service is available..."
    if ! docker compose -f "$COMPOSE_FILE" ps backend | grep -q "Up\|running"; then
        echo "⚠️  Backend service not running, starting temporarily for migration check..."
        docker compose -f "$COMPOSE_FILE" up -d backend
        sleep 10
    fi
    
    # Try to get current migration with error handling
    echo "🔍 Getting current migration..."
    CURRENT_MIGRATION=$(docker compose -f "$COMPOSE_FILE" run --rm backend alembic current 2>&1)
    CURRENT_EXIT_CODE=$?
    
    if [ $CURRENT_EXIT_CODE -ne 0 ]; then
        echo "❌ Failed to get current migration status (exit code: $CURRENT_EXIT_CODE)"
        echo "Alembic current output: $CURRENT_MIGRATION"
        
        # Check if it's a database connection issue
        if echo "$CURRENT_MIGRATION" | grep -qi "connection\|database\|psycopg2"; then
            echo "🔍 Database connection issue detected. Checking database status..."
            docker compose -f "$COMPOSE_FILE" ps db
            docker compose -f "$COMPOSE_FILE" logs db --tail=10
        fi
        
        return 1
    fi
    echo "Current migration: $CURRENT_MIGRATION"
    
    # Try to get latest head with error handling
    echo "🔍 Getting latest migration head..."
    LATEST_HEAD=$(docker compose -f "$COMPOSE_FILE" run --rm backend alembic heads 2>&1)
    HEADS_EXIT_CODE=$?
    
    if [ $HEADS_EXIT_CODE -ne 0 ]; then
        echo "❌ Failed to get latest migration head (exit code: $HEADS_EXIT_CODE)"
        echo "Alembic heads output: $LATEST_HEAD"
        return 1
    fi
    echo "Latest available migration: $LATEST_HEAD"
    
    # Check if migrations are pending
    PENDING_MIGRATIONS=$(docker compose -f "$COMPOSE_FILE" run --rm backend alembic history --verbose 2>/dev/null | grep -c "Rev:" || echo "0")
    echo "Total migrations available: $PENDING_MIGRATIONS"
    
    return 0
}

# Function to resolve migration conflicts automatically
resolve_migration_conflicts() {
    echo "🔧 Attempting to resolve migration conflicts..."
    echo "⚠️  WARNING: This will modify the alembic_version table"
    
    # Create full database backup first (additional safety)
    echo "💾 Creating emergency database backup before conflict resolution..."
    EMERGENCY_BACKUP="emergency_backup_$(date +%Y%m%d_%H%M%S).sql"
    if docker compose -f "$COMPOSE_FILE" exec db pg_dump -U "$DB_USER" "$DB_NAME" > "$EMERGENCY_BACKUP" 2>/dev/null; then
        echo "✅ Emergency backup created: $EMERGENCY_BACKUP"
    else
        echo "❌ CRITICAL: Could not create emergency backup"
        echo "🛑 ABORTING conflict resolution for safety"
        return 1
    fi
    
    # Backup current alembic_version state
    echo "💾 Backing up current migration state..."
    docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE TABLE IF NOT EXISTS alembic_version_backup_$(date +%Y%m%d_%H%M%S) AS SELECT * FROM alembic_version;" >/dev/null 2>&1 || true
    
    # Show current conflicts for logging
    echo "🔍 Current migration conflicts:"
    docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT version_num FROM alembic_version ORDER BY version_num;"
    
    # Clear conflicting entries
    echo "🧹 Clearing conflicting migration entries..."
    docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -c "DELETE FROM alembic_version;"
    
    # Determine correct migration to stamp - find the most recent merge migration
    # Try to find the latest merge migration first, then fall back to known safe migrations
    if docker compose -f "$COMPOSE_FILE" run --rm backend alembic history | grep -q "f4932fcd0940"; then
        STAMP_TARGET="f4932fcd0940"
        echo "📌 Stamping with RECENT MERGE migration: $STAMP_TARGET"
    elif docker compose -f "$COMPOSE_FILE" run --rm backend alembic history | grep -q "1a1177e7cad1"; then
        STAMP_TARGET="1a1177e7cad1"
        echo "📌 Stamping with OLDER MERGE migration: $STAMP_TARGET"
    elif docker compose -f "$COMPOSE_FILE" run --rm backend alembic history | grep -q "1e57d07d1eb9"; then
        STAMP_TARGET="1e57d07d1eb9"
        echo "📌 Stamping with KNOWN SAFE production migration: $STAMP_TARGET"
    else
        echo "❌ CRITICAL: Cannot find known production migrations (f4932fcd0940, 1a1177e7cad1 or 1e57d07d1eb9)"
        echo "🛑 Manual intervention required - not safe to auto-resolve"
        echo "💾 Emergency backup available at: $EMERGENCY_BACKUP"
        return 1
    fi
    
    # Stamp with the safe migration
    if docker compose -f "$COMPOSE_FILE" run --rm backend alembic stamp "$STAMP_TARGET"; then
        echo "✅ Successfully stamped with $STAMP_TARGET"
    else
        echo "❌ CRITICAL: Failed to stamp migration"
        echo "💾 Emergency backup available at: $EMERGENCY_BACKUP"
        return 1
    fi
    
    # Verify resolution
    if check_migration_conflicts; then
        echo "✅ Migration conflicts resolved successfully"
        echo "🗑️  Cleaning up emergency backup (conflict resolved safely)"
        rm -f "$EMERGENCY_BACKUP" || true
        return 0
    else
        echo "❌ Failed to resolve migration conflicts"
        echo "💾 Emergency backup preserved at: $EMERGENCY_BACKUP"
        return 1
    fi
}

# Function to create database backup
create_migration_backup() {
    echo "💾 Creating database backup before migration..."
    
    BACKUP_FILE="migration_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if docker compose -f "$COMPOSE_FILE" exec db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
        echo "✅ Database backup created: $BACKUP_FILE"
        echo "BACKUP_FILE=$BACKUP_FILE" >> $GITHUB_OUTPUT 2>/dev/null || true
    else
        echo "⚠️  Database backup failed, continuing without backup"
    fi
}

# Function to validate migration safety
validate_migration_safety() {
    echo "🛡️  Validating migration safety..."
    
    # Check for destructive operations in pending migrations
    PENDING_MIGRATIONS=$(docker compose -f "$COMPOSE_FILE" run --rm backend alembic history -r current:head 2>/dev/null || echo "")
    
    if echo "$PENDING_MIGRATIONS" | grep -qi "drop\|delete\|truncate"; then
        echo "⚠️  WARNING: Potentially destructive migration operations detected"
        echo "Pending migrations contain DROP, DELETE, or TRUNCATE operations"
        echo "Consider manual review before proceeding"
        # Don't fail here, just warn
    fi
    
    echo "✅ Migration safety validation complete"
}

# Function to apply migrations with monitoring and rollback capability
apply_migrations_safely() {
    echo "⬆️  Applying migrations with monitoring and rollback capability..."
    
    # Record current migration state before applying
    CURRENT_MIGRATION=$(docker compose -f "$COMPOSE_FILE" run --rm backend alembic current 2>/dev/null | head -1 || echo "unknown")
    echo "📋 Current migration before applying: $CURRENT_MIGRATION"
    
    # Check if we have a recent backup for potential rollback
    LATEST_BACKUP=$(ls -t migration_backup_*.sql 2>/dev/null | head -1 || echo "")
    if [ -n "$LATEST_BACKUP" ]; then
        echo "💾 Rollback backup available: $LATEST_BACKUP"
    else
        echo "⚠️  No recent backup found - creating one now"
        create_migration_backup
        LATEST_BACKUP=$(ls -t migration_backup_*.sql 2>/dev/null | head -1)
    fi
    
    # Start migration with timeout (5 minutes)
    echo "⏱️  Starting migration with 5-minute timeout..."
    timeout 300 docker compose -f "$COMPOSE_FILE" run --rm backend alembic upgrade heads > migration_output.log 2>&1
    MIGRATION_EXIT_CODE=$?
    
    echo "Migration output:"
    cat migration_output.log
    
    if [ $MIGRATION_EXIT_CODE -eq 0 ]; then
        echo "✅ Migrations applied successfully"
        
        # Verify final state
        FINAL_STATE=$(docker compose -f "$COMPOSE_FILE" run --rm backend alembic current 2>&1)
        echo "Final migration state: $FINAL_STATE"
        
        # Test basic database connectivity
        echo "🔍 Testing database connectivity after migration..."
        if docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM users;" >/dev/null 2>&1; then
            echo "✅ Database is accessible and responsive"
        else
            echo "❌ CRITICAL: Database appears corrupted after migration"
            echo "🔄 Consider rollback using: $LATEST_BACKUP"
            return 1
        fi
        
        return 0
    elif [ $MIGRATION_EXIT_CODE -eq 124 ]; then
        echo "❌ Migration TIMED OUT after 5 minutes"
        echo "🛑 This could indicate a deadlock or hanging migration"
        echo "🔍 Current database state:"
        docker compose -f "$COMPOSE_FILE" run --rm backend alembic current 2>&1 || true
        echo "💾 Rollback backup available: $LATEST_BACKUP"
        return 1
    else
        echo "❌ Migration failed with exit code $MIGRATION_EXIT_CODE"
        
        # Show current state for debugging
        echo "🔍 Current database state:"
        docker compose -f "$COMPOSE_FILE" run --rm backend alembic current 2>&1 || true
        
        # Check if database is still responsive
        echo "🔍 Testing database connectivity after failed migration..."
        if docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
            echo "✅ Database is still responsive"
        else
            echo "❌ CRITICAL: Database appears unresponsive"
            echo "💾 IMMEDIATE ROLLBACK RECOMMENDED using: $LATEST_BACKUP"
        fi
        
        echo "💾 Rollback backup available: $LATEST_BACKUP"
        return 1
    fi
}

# Main execution
main() {
    echo "🚀 Starting migration validation and application..."
    
    # Initialize migration failure tracking
    MIGRATION_FAILED=false
    
    # Step 1: Check database connection
    if ! check_db_connection; then
        echo "❌ Database connection failed"
        exit 1
    fi
    
    # Step 2: Check for conflicts
    if ! check_migration_conflicts; then
        echo "⚠️  Migration conflicts detected, attempting resolution..."
        if ! resolve_migration_conflicts; then
            echo "⚠️  Could not resolve migration conflicts - will continue with current state"
            echo "💡 Manual intervention may be required"
            MIGRATION_FAILED=true
        fi
    fi
    
    # Step 3: Get migration status
    if ! get_migration_status; then
        echo "⚠️  Failed to get migration status - continuing with deployment"
        echo "💡 Migration state may need manual verification"
        MIGRATION_FAILED=${MIGRATION_FAILED:-true}
    fi
    
    # Step 4: Validate safety
    validate_migration_safety
    
    # Step 5: Create backup
    create_migration_backup
    
    # Step 6: Apply migrations
    if ! apply_migrations_safely; then
        echo "⚠️  Migration application failed - continuing with deployment"
        echo "🔄 The application will start with current database state"
        echo "💡 Manual migration may be required after deployment"
        MIGRATION_FAILED=true
    fi
    
    # Final summary
    if [ "$MIGRATION_FAILED" = true ]; then
        echo "⚠️  ⚠️  ⚠️  DEPLOYMENT WARNING ⚠️  ⚠️  ⚠️"
        echo "✅ Migration validation completed with WARNINGS"
        echo "⚠️  Database migrations failed but deployment will continue"
        echo "📝 Action required: Check migration state manually after deployment"
        echo "💾 Rollback available if needed"
        echo "⚠️  ⚠️  ⚠️  END WARNING ⚠️  ⚠️  ⚠️"
        exit 2  # Exit code 2 = warning (not failure)
    else
        echo "🎉 Migration validation and application completed successfully!"
        exit 0  # Success
    fi
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
