"""
Supabase authentication integration for the python_agent app.

This module provides integration with Supabase authentication,
enabling user authentication and authorization capabilities.
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.backends import BaseBackend

logger = logging.getLogger(__name__)


class SupabaseAuthClient:
    """
    Client for interacting with Supabase authentication.
    
    This client provides methods for authenticating users with Supabase,
    managing user sessions, and handling user data.
    """
    
    def __init__(self, url=None, api_key=None):
        """
        Initialize the Supabase authentication client.
        
        Args:
            url: Supabase URL
            api_key: Supabase API key
        """
        supabase_config = getattr(settings, 'SUPABASE_CONFIG', {})
        
        self.url = url or supabase_config.get('url', '')
        self.api_key = api_key or supabase_config.get('api_key', '')
        
        if not self.url or not self.api_key:
            logger.warning("Supabase URL or API key not provided. Authentication will not work.")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Supabase API requests.
        
        Returns:
            Dict[str, str]: Headers for Supabase API requests
        """
        return {
            'apikey': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _get_auth_headers(self, access_token: str) -> Dict[str, str]:
        """
        Get headers for authenticated Supabase API requests.
        
        Args:
            access_token: Access token for authentication
            
        Returns:
            Dict[str, str]: Headers for authenticated Supabase API requests
        """
        headers = self._get_headers()
        headers['Authorization'] = f"Bearer {access_token}"
        return headers
    
    def sign_up(self, email: str, password: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sign up a new user.
        
        Args:
            email: User email
            password: User password
            metadata: Additional user metadata
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/auth/v1/signup"
            
            payload = {
                'email': email,
                'password': password,
                'data': metadata or {}
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error signing up user: {e}")
            return {'error': str(e)}
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in a user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/auth/v1/token?grant_type=password"
            
            payload = {
                'email': email,
                'password': password
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error signing in user: {e}")
            return {'error': str(e)}
    
    def sign_out(self, access_token: str) -> Dict[str, Any]:
        """
        Sign out a user.
        
        Args:
            access_token: Access token for authentication
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/auth/v1/logout"
            
            response = requests.post(
                url,
                headers=self._get_auth_headers(access_token)
            )
            
            response.raise_for_status()
            
            return {'status': 'success'}
        
        except Exception as e:
            logger.error(f"Error signing out user: {e}")
            return {'error': str(e)}
    
    def get_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get user data.
        
        Args:
            access_token: Access token for authentication
            
        Returns:
            Dict[str, Any]: User data
        """
        try:
            url = f"{self.url}/auth/v1/user"
            
            response = requests.get(
                url,
                headers=self._get_auth_headers(access_token)
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return {'error': str(e)}
    
    def update_user(self, access_token: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user data.
        
        Args:
            access_token: Access token for authentication
            data: User data to update
            
        Returns:
            Dict[str, Any]: Updated user data
        """
        try:
            url = f"{self.url}/auth/v1/user"
            
            response = requests.put(
                url,
                headers=self._get_auth_headers(access_token),
                json=data
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error updating user data: {e}")
            return {'error': str(e)}
    
    def reset_password_request(self, email: str) -> Dict[str, Any]:
        """
        Request a password reset.
        
        Args:
            email: User email
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/auth/v1/recover"
            
            payload = {
                'email': email
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return {'status': 'success'}
        
        except Exception as e:
            logger.error(f"Error requesting password reset: {e}")
            return {'error': str(e)}
    
    def reset_password(self, access_token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset a user's password.
        
        Args:
            access_token: Access token for authentication
            new_password: New password
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/auth/v1/user"
            
            payload = {
                'password': new_password
            }
            
            response = requests.put(
                url,
                headers=self._get_auth_headers(access_token),
                json=payload
            )
            
            response.raise_for_status()
            
            return {'status': 'success'}
        
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return {'error': str(e)}
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dict[str, Any]: New access token
        """
        try:
            url = f"{self.url}/auth/v1/token?grant_type=refresh_token"
            
            payload = {
                'refresh_token': refresh_token
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return {'error': str(e)}
    
    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """
        Get user data by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: User data
        """
        try:
            url = f"{self.url}/rest/v1/users?id=eq.{user_id}"
            
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            
            users = response.json()
            
            if not users:
                return {'error': 'User not found'}
            
            return users[0]
        
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return {'error': str(e)}


class SupabaseAuthBackend(BaseBackend):
    """
    Django authentication backend for Supabase.
    
    This backend authenticates users with Supabase and creates
    corresponding Django users.
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        """
        Authenticate a user with Supabase.
        
        Args:
            request: HTTP request
            email: User email
            password: User password
            
        Returns:
            User: Authenticated user, or None if authentication failed
        """
        if not email or not password:
            return None
        
        client = SupabaseAuthClient()
        response = client.sign_in(email, password)
        
        if 'error' in response:
            return None
        
        user_data = client.get_user(response.get('access_token', ''))
        
        if 'error' in user_data:
            return None
        
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=None  # Don't store the password in Django
            )
            
            user.first_name = user_data.get('user_metadata', {}).get('first_name', '')
            user.last_name = user_data.get('user_metadata', {}).get('last_name', '')
            user.save()
        
        if request:
            request.session['supabase_access_token'] = response.get('access_token', '')
            request.session['supabase_refresh_token'] = response.get('refresh_token', '')
        
        return user
    
    def get_user(self, user_id):
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User: User with the specified ID, or None if not found
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


supabase_auth_client = SupabaseAuthClient()
