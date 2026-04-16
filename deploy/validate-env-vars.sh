#!/bin/bash

# Environment Variables Validation Script
# Validates that all required environment variables are set and properly formatted

set -e

ENV_FILE="${ENV_FILE:-.env}"
ERRORS=0

echo "🔍 Validating environment variables from: $ENV_FILE"

# Function to check if a variable is set and not empty
check_var() {
    local var_name="$1"
    local required="$2"  # "required" or "optional"
    local var_type="$3"  # "string" or "integer"
    
    # Load the variable from .env file if it exists
    if [ -f "$ENV_FILE" ]; then
        local var_value=$(grep "^${var_name}=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/^["'\'']//' | sed 's/["'\'']$//')
    else
        local var_value="${!var_name}"  # Get from environment
    fi
    
    # Check if required variable is missing or empty
    if [ "$required" = "required" ]; then
        if [ -z "$var_value" ]; then
            echo "❌ ERROR: Required variable $var_name is not set or empty"
            ((ERRORS++))
            return 1
        fi
    fi
    
    # Validate integer type
    if [ "$var_type" = "integer" ] && [ -n "$var_value" ]; then
        if ! [[ "$var_value" =~ ^[0-9]+$ ]]; then
            echo "❌ ERROR: Variable $var_name must be an integer, got: '$var_value'"
            ((ERRORS++))
            return 1
        fi
    fi
    
    # Variable is OK
    if [ -n "$var_value" ]; then
        if [ "$var_type" = "integer" ]; then
            echo "✅ $var_name = $var_value"
        else
            # Mask sensitive values
            if [[ "$var_name" =~ (SECRET|PASSWORD|KEY|TOKEN) ]]; then
                echo "✅ $var_name = ****"
            else
                echo "✅ $var_name = ${var_value:0:30}..."
            fi
        fi
    else
        echo "⚠️  $var_name = (using default)"
    fi
    
    return 0
}

echo ""
echo "📋 Checking Database Configuration..."
check_var "DATABASE_URL" "required" "string"
check_var "POSTGRES_DB" "required" "string"
check_var "POSTGRES_USER" "required" "string"
check_var "POSTGRES_PASSWORD" "required" "string"

echo ""
echo "📋 Checking Redis & Celery Configuration..."
check_var "CELERY_BROKER_URL" "required" "string"
check_var "CELERY_RESULT_BACKEND" "required" "string"

echo ""
echo "📋 Checking MinIO Configuration..."
check_var "MINIO_ROOT_USER" "required" "string"
check_var "MINIO_ROOT_PASSWORD" "required" "string"
check_var "MINIO_INTERNAL_URL" "optional" "string"
check_var "MINIO_PUBLIC_URL" "optional" "string"

echo ""
echo "📋 Checking Allegro API Configuration..."
check_var "ALLEGRO_CLIENT_ID" "required" "string"
check_var "ALLEGRO_CLIENT_SECRET" "required" "string"

echo ""
echo "📋 Checking JWT Configuration..."
check_var "SECRET_KEY" "required" "string"
check_var "ACCESS_TOKEN_EXPIRE_MINUTES" "optional" "integer"
check_var "REFRESH_TOKEN_EXPIRE_DAYS" "optional" "integer"

echo ""
echo "📋 Checking Email Configuration..."
check_var "MAIL_SERVER" "optional" "string"
check_var "MAIL_USERNAME" "optional" "string"
check_var "MAIL_PASSWORD" "optional" "string"
check_var "MAIL_FROM" "optional" "string"

echo ""
echo "📋 Checking Google OAuth Configuration..."
check_var "GOOGLE_CLIENT_ID" "optional" "string"
check_var "GOOGLE_CLIENT_SECRET" "optional" "string"

echo ""
echo "📋 Checking Asystenciai Integration..."
check_var "ASYSTENCIAI_SHARED_SECRET" "optional" "string"
check_var "ASYSTENCIAI_SETUP_TOKEN_EXPIRE_MINUTES" "optional" "integer"
check_var "GEMINI_API_KEY" "optional" "string"
check_var "ANTHROPIC_API_KEY" "optional" "string"

echo ""
echo "📋 Checking Frontend Configuration..."
check_var "FRONTEND_URL" "optional" "string"

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ All environment variables are valid!"
    exit 0
else
    echo "❌ Found $ERRORS error(s) in environment variables"
    echo ""
    echo "💡 To fix:"
    echo "   1. Check your .env.prod file on the server"
    echo "   2. Compare with deploy/env.prod.example"
    echo "   3. Add missing variables with proper values"
    exit 1
fi

