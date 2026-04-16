#!/bin/bash

# Script to update .env.prod file with missing variables from template
# Usage: ./deploy/update-env-prod.sh

set -e

ENV_FILE="${ENV_FILE:-.env.prod}"
TEMPLATE_FILE="${TEMPLATE_FILE:-deploy/env.prod.example}"

echo "🔧 Updating $ENV_FILE with missing variables from $TEMPLATE_FILE"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Template file $TEMPLATE_FILE not found!"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found!"
    echo "Creating new file from template..."
    cp "$TEMPLATE_FILE" "$ENV_FILE"
    echo "✅ Created $ENV_FILE from template"
    echo "⚠️  IMPORTANT: Update the file with actual production values!"
    exit 0
fi

# Create backup
BACKUP_FILE="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$ENV_FILE" "$BACKUP_FILE"
echo "💾 Backup created: $BACKUP_FILE"

# Track changes
ADDED_COUNT=0
UPDATED_COUNT=0

# Read template line by line
while IFS= read -r line; do
    # Skip comments and empty lines
    if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
        continue
    fi
    
    # Extract variable name
    if [[ "$line" =~ ^([A-Z_]+)= ]]; then
        VAR_NAME="${BASH_REMATCH[1]}"
        
        # Check if variable exists in env file
        if ! grep -q "^${VAR_NAME}=" "$ENV_FILE"; then
            echo "➕ Adding missing variable: $VAR_NAME"
            echo "$line" >> "$ENV_FILE"
            ((ADDED_COUNT++))
        fi
    fi
done < "$TEMPLATE_FILE"

echo ""
if [ $ADDED_COUNT -gt 0 ]; then
    echo "✅ Added $ADDED_COUNT missing variable(s) to $ENV_FILE"
    echo "⚠️  IMPORTANT: Review and update the new variables with actual values!"
    echo ""
    echo "New variables added:"
    grep -vFf "$BACKUP_FILE" "$ENV_FILE" | grep "^[A-Z_]*=" || echo "  (none with default pattern)"
else
    echo "✅ No missing variables found - $ENV_FILE is up to date"
fi

echo ""
echo "📋 To review changes:"
echo "   diff $BACKUP_FILE $ENV_FILE"
echo ""
echo "📋 To restore from backup:"
echo "   cp $BACKUP_FILE $ENV_FILE"

