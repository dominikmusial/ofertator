#!/bin/bash

# Emergency Database Rollback Script
# Use this ONLY in case of catastrophic migration failure

set -e

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
DB_USER="${DB_USER:-user}"
DB_NAME="${DB_NAME:-allegro_bot_prod}"

echo "🚨 EMERGENCY DATABASE ROLLBACK SCRIPT"
echo "⚠️  WARNING: This will completely restore the database from backup"
echo "⚠️  ALL DATA SINCE BACKUP WILL BE LOST!"
echo ""

# Function to list available backups
list_backups() {
    echo "📋 Available backup files:"
    ls -la migration_backup_*.sql emergency_backup_*.sql 2>/dev/null | sort -k9 -r || echo "No backup files found"
    echo ""
}

# Function to validate backup file
validate_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        echo "❌ Backup file not found: $backup_file"
        return 1
    fi
    
    # Check if file is not empty
    if [ ! -s "$backup_file" ]; then
        echo "❌ Backup file is empty: $backup_file"
        return 1
    fi
    
    # Check if it looks like a valid SQL dump
    if ! head -10 "$backup_file" | grep -q "PostgreSQL database dump"; then
        echo "❌ File does not appear to be a valid PostgreSQL dump"
        return 1
    fi
    
    echo "✅ Backup file appears valid"
    return 0
}

# Function to perform emergency rollback
perform_rollback() {
    local backup_file="$1"
    
    echo "🛑 PERFORMING EMERGENCY ROLLBACK"
    echo "📁 Using backup: $backup_file"
    echo ""
    
    # Create a backup of current state before rollback
    echo "💾 Creating backup of current state before rollback..."
    CURRENT_BACKUP="pre_rollback_backup_$(date +%Y%m%d_%H%M%S).sql"
    docker compose -f "$COMPOSE_FILE" exec db pg_dump -U "$DB_USER" "$DB_NAME" > "$CURRENT_BACKUP" 2>/dev/null || echo "⚠️ Could not backup current state"
    
    # Stop backend to prevent connections during rollback
    echo "⏹️  Stopping backend service..."
    docker compose -f "$COMPOSE_FILE" stop backend worker || true
    
    # Drop and recreate database
    echo "🗑️  Dropping current database..."
    docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME}_temp;" 2>/dev/null || true
    docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -c "ALTER DATABASE $DB_NAME RENAME TO ${DB_NAME}_temp;"
    docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
    
    # Restore from backup
    echo "🔄 Restoring database from backup..."
    if docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$DB_USER" -d "$DB_NAME" < "$backup_file"; then
        echo "✅ Database restored successfully"
        
        # Drop the temporary backup
        docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -c "DROP DATABASE ${DB_NAME}_temp;" 2>/dev/null || true
        
        # Verify restoration
        echo "🔍 Verifying database restoration..."
        USER_COUNT=$(docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' \t\n\r' || echo "0")
        echo "Users in restored database: $USER_COUNT"
        
        if [ "$USER_COUNT" -gt 0 ]; then
            echo "✅ Database appears to be restored correctly"
        else
            echo "⚠️  Database may not be fully restored (no users found)"
        fi
        
        # Restart services
        echo "🚀 Restarting services..."
        docker compose -f "$COMPOSE_FILE" up -d
        
        echo ""
        echo "🎉 ROLLBACK COMPLETED"
        echo "📁 Current state backup saved as: $CURRENT_BACKUP"
        echo "🔍 Please verify application functionality"
        
    else
        echo "❌ CRITICAL: Database restoration failed"
        echo "🔄 Attempting to restore original database..."
        docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -c "DROP DATABASE $DB_NAME;" 2>/dev/null || true
        docker compose -f "$COMPOSE_FILE" exec db psql -U "$DB_USER" -c "ALTER DATABASE ${DB_NAME}_temp RENAME TO $DB_NAME;" 2>/dev/null || true
        echo "💾 Current state backup preserved as: $CURRENT_BACKUP"
        return 1
    fi
}

# Function to show rollback instructions
show_instructions() {
    echo "📋 EMERGENCY ROLLBACK INSTRUCTIONS"
    echo ""
    echo "1. List available backups:"
    echo "   $0 --list"
    echo ""
    echo "2. Perform rollback with specific backup:"
    echo "   $0 --rollback backup_file.sql"
    echo ""
    echo "3. Interactive mode (recommended):"
    echo "   $0 --interactive"
    echo ""
    echo "⚠️  IMPORTANT SAFETY NOTES:"
    echo "   - This will PERMANENTLY delete current data"
    echo "   - Only use in case of catastrophic failure"
    echo "   - Always verify backup file before using"
    echo "   - Consider consulting team before rollback"
    echo ""
}

# Interactive rollback mode
interactive_rollback() {
    echo "🔄 INTERACTIVE ROLLBACK MODE"
    echo ""
    
    list_backups
    
    echo "⚠️  WARNING: This will permanently delete current database data!"
    echo "Only proceed if you're certain this is necessary."
    echo ""
    read -p "Do you want to continue? (type 'YES' to proceed): " confirm
    
    if [ "$confirm" != "YES" ]; then
        echo "❌ Rollback cancelled"
        exit 0
    fi
    
    echo ""
    read -p "Enter the backup filename to restore: " backup_file
    
    if validate_backup "$backup_file"; then
        echo ""
        echo "📁 You selected: $backup_file"
        echo "⚠️  FINAL WARNING: This will delete all current data!"
        read -p "Type 'ROLLBACK' to confirm: " final_confirm
        
        if [ "$final_confirm" = "ROLLBACK" ]; then
            perform_rollback "$backup_file"
        else
            echo "❌ Rollback cancelled"
            exit 0
        fi
    else
        echo "❌ Invalid backup file"
        exit 1
    fi
}

# Main execution
case "$1" in
    --list)
        list_backups
        ;;
    --rollback)
        if [ -z "$2" ]; then
            echo "❌ Error: Backup file not specified"
            echo "Usage: $0 --rollback backup_file.sql"
            exit 1
        fi
        
        if validate_backup "$2"; then
            perform_rollback "$2"
        else
            exit 1
        fi
        ;;
    --interactive)
        interactive_rollback
        ;;
    --help|-h|"")
        show_instructions
        ;;
    *)
        echo "❌ Unknown option: $1"
        show_instructions
        exit 1
        ;;
esac
