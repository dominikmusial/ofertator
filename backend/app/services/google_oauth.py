from google.auth.transport import requests
from google.oauth2 import id_token
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

class GoogleOAuthService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        
    async def verify_google_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Google ID token and return user info"""
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            # Ensure email is verified
            if not idinfo.get('email_verified', False):
                raise ValueError('Email not verified by Google.')
            
            # Extract user information
            user_info = {
                'sub': idinfo['sub'],  # Google user ID
                'email': idinfo['email'],
                'given_name': idinfo.get('given_name', ''),
                'family_name': idinfo.get('family_name', ''),
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False)
            }
            
            return user_info
            
        except ValueError as e:
            print(f"Google token verification failed: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error in Google token verification: {str(e)}")
            return None
    
    async def exchange_code_for_token(self, authorization_code: str) -> Optional[str]:
        """Exchange authorization code for access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'code': authorization_code,
                        'grant_type': 'authorization_code',
                        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                    }
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    return token_data.get('id_token')
                else:
                    print(f"Google token exchange failed: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error exchanging Google code for token: {str(e)}")
            return None
    
    def get_authorization_url(self) -> str:
        """Get Google OAuth authorization URL"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': self.client_id,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'offline',
            'hd': 'vsprint.pl'  # Restrict to vsprint domain
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    def validate_vsprint_domain(self, email: str) -> bool:
        """Validate that email belongs to vsprint.pl domain"""
        return email.endswith('@vsprint.pl')

# Singleton instance
google_oauth_service = GoogleOAuthService() 