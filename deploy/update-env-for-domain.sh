#!/bin/bash

# Update environment variables for domain deployment
set -e

DOMAIN="ofertator.vautomate.pl"
HTTPS_URL="https://$DOMAIN"

echo "🔧 Updating environment variables for domain: $DOMAIN"

# Update .env file
if [ -f ".env" ]; then
    echo "📝 Updating .env file..."
    
    # Update FRONTEND_URL
    if grep -q "FRONTEND_URL=" .env; then
        sed -i.bak "s|FRONTEND_URL=.*|FRONTEND_URL=$HTTPS_URL|" .env
    else
        echo "FRONTEND_URL=$HTTPS_URL" >> .env
    fi
    
    # Update GOOGLE_REDIRECT_URI
    if grep -q "GOOGLE_REDIRECT_URI=" .env; then
        sed -i.bak "s|GOOGLE_REDIRECT_URI=.*|GOOGLE_REDIRECT_URI=$HTTPS_URL/auth/google/callback|" .env
    else
        echo "GOOGLE_REDIRECT_URI=$HTTPS_URL/auth/google/callback" >> .env
    fi
    
    # Update VITE_GOOGLE_CLIENT_ID (ensure it's on a separate line)
    if grep -q "VITE_GOOGLE_CLIENT_ID=" .env; then
        # Remove the DOMAIN line that might be appended to VITE_GOOGLE_CLIENT_ID
        sed -i.bak '/VITE_GOOGLE_CLIENT_ID=.*DOMAIN=/d' .env
        # Ensure VITE_GOOGLE_CLIENT_ID is properly set
        sed -i.bak 's|VITE_GOOGLE_CLIENT_ID=.*|VITE_GOOGLE_CLIENT_ID=456288647414-n28roh6se80ir8shubos0jlu1k0quguj.apps.googleusercontent.com|' .env
    fi
    
    echo "✅ .env file updated successfully"
else
    echo "❌ .env file not found"
    exit 1
fi

echo ""
echo "📋 Updated configuration:"
echo "   FRONTEND_URL: $HTTPS_URL"
echo "   GOOGLE_REDIRECT_URI: $HTTPS_URL/auth/google/callback"
echo ""
echo "🔄 Next steps:"
echo "1. Copy the updated .env file to your VM"
echo "2. Restart your containers on the VM"
echo "3. Set up DNS records for $DOMAIN -> 83.6.162.106"
echo "4. Run SSL setup: ./deploy/setup-ssl.sh $DOMAIN admin@vsprint.pl" 