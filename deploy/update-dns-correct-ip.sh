#!/bin/bash

# Update DNS configuration with correct VM IP
set -e

DOMAIN="ofertator.vautomate.pl"
CORRECT_VM_IP="34.140.91.224"
HTTPS_URL="https://$DOMAIN"

echo "🔧 Correcting DNS configuration for Bot-Sok"
echo "================================"
echo "📝 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Correct VM IP: $CORRECT_VM_IP"
echo "   HTTPS URL: $HTTPS_URL"
echo ""

echo "❗ IMPORTANT: Update your CyberFolks DNS panel:"
echo "   1. Remove the A record pointing to 83.6.162.106"
echo "   2. Keep/Update the A record pointing to $CORRECT_VM_IP"
echo "   3. Remove any other conflicting A records"
echo ""

echo "🎯 Correct DNS Configuration:"
echo "=================================="
echo "Domain: $DOMAIN"
echo "Type: A"
echo "Name: @ (or leave empty)"
echo "Value: $CORRECT_VM_IP"
echo "TTL: 300"
echo ""

echo "🔍 After updating DNS, test with:"
echo "   nslookup $DOMAIN"
echo "   Should return only: $CORRECT_VM_IP"
echo ""

echo "🔄 Then connect to VM:"
echo "   ssh sokol@$CORRECT_VM_IP"
echo ""

echo "📂 Copy files to VM:"
echo "   scp .env frontend/nginx.conf sokol@$CORRECT_VM_IP:~/bot-sok/"
echo ""

echo "🚀 Restart containers on VM:"
echo "   ssh sokol@$CORRECT_VM_IP"
echo "   cd ~/bot-sok"
echo "   docker-compose down"
echo "   docker-compose up -d" 