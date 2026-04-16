#!/bin/bash

# Automatically merge new variables from template into existing .env.prod
# This runs during deployment to ensure all new variables are present
# while preserving existing production values

set -e
set -o pipefail

# Trap errors and show where they occurred
trap 'echo "❌ Error on line $LINENO. Exit code: $?"' ERR

ENV_FILE="${ENV_FILE:-.env.prod}"
TEMPLATE_FILE="${TEMPLATE_FILE:-deploy/env.prod.example}"
MERGED_FILE="${ENV_FILE}.merged"

echo "🔄 Auto-merging environment variables..."
echo "   Template: $TEMPLATE_FILE"
echo "   Existing: $ENV_FILE"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Template file $TEMPLATE_FILE not found!"
    exit 1
fi

# If .env.prod doesn't exist, create from template
if [ ! -f "$ENV_FILE" ]; then
    echo "📄 Creating $ENV_FILE from template (first deployment)"
    cp "$TEMPLATE_FILE" "$ENV_FILE"
    echo "⚠️  IMPORTANT: Review and update with production values!"
    exit 0
fi

# Create backup
BACKUP_FILE="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$ENV_FILE" "$BACKUP_FILE"
echo "💾 Backup: $BACKUP_FILE"

# Start with existing file
cp "$ENV_FILE" "$MERGED_FILE"

ADDED_COUNT=0
UNCHANGED_COUNT=0

echo ""
echo "🔍 Processing variables from template..."

# Read template line by line
while IFS= read -r line; do
    # Preserve comments and empty lines from template
    if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
        continue
    fi
    
    # Extract variable name and value from template
    if [[ "$line" =~ ^([A-Z_][A-Z0-9_]*)=(.*)$ ]]; then
        VAR_NAME="${BASH_REMATCH[1]}"
        TEMPLATE_VALUE="${BASH_REMATCH[2]}"
        
        # Check if variable exists in current .env.prod
        if grep -q "^${VAR_NAME}=" "$ENV_FILE"; then
            # Variable exists - keep existing value
            UNCHANGED_COUNT=$((UNCHANGED_COUNT + 1))
        else
            # Variable missing - add from template
            echo "➕ Adding: $VAR_NAME (from template)"
            echo "$line" >> "$MERGED_FILE"
            ADDED_COUNT=$((ADDED_COUNT + 1))
        fi
    fi
done < "$TEMPLATE_FILE"

echo ""
if [ $ADDED_COUNT -gt 0 ]; then
    # Replace old file with merged version
    mv "$MERGED_FILE" "$ENV_FILE"
    echo "✅ Merged successfully!"
    echo "   - Added: $ADDED_COUNT new variable(s)"
    echo "   - Unchanged: $UNCHANGED_COUNT existing variable(s)"
    echo ""
    echo "📋 New variables added (review these):"
    echo "---"
    # Show only the newly added lines (disable exit on error for diff)
    set +e
    diff "$BACKUP_FILE" "$ENV_FILE" | grep "^>" | sed 's/^> /   /'
    DIFF_EXIT=$?
    set -e
    if [ $DIFF_EXIT -ne 0 ] && [ $DIFF_EXIT -ne 1 ]; then
        echo "   (unable to show diff)"
    fi
    echo "---"
    echo ""
    echo "💡 Backup available at: $BACKUP_FILE"
    exit 0
else
    # No changes needed
    rm -f "$MERGED_FILE"
    echo "✅ No new variables found - .env.prod is up to date!"
    echo "   - Total variables: $UNCHANGED_COUNT"
    # Clean up backup since nothing changed
    rm -f "$BACKUP_FILE"
    exit 0
fi

