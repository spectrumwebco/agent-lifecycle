"""
Supabase functions integration for the python_agent app.

This module provides integration with Supabase functions,
enabling serverless function execution capabilities.
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from django.conf import settings

logger = logging.getLogger(__name__)


class SupabaseFunctionsClient:
    """
    Client for interacting with Supabase functions.
    
    This client provides methods for invoking Supabase Edge Functions,
    which are serverless functions that run on the edge.
    """
    
    def __init__(self, url=None, api_key=None):
        """
        Initialize the Supabase functions client.
        
        Args:
            url: Supabase URL
            api_key: Supabase API key
        """
        supabase_config = getattr(settings, 'SUPABASE_CONFIG', {})
        
        self.url = url or supabase_config.get('url', '')
        self.api_key = api_key or supabase_config.get('api_key', '')
        
        if not self.url or not self.api_key:
            logger.warning("Supabase URL or API key not provided. Functions will not work.")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Supabase API requests.
        
        Returns:
            Dict[str, str]: Headers for Supabase API requests
        """
        return {
            'apikey': self.api_key,
            'Authorization': f"Bearer {self.api_key}",
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
    
    def invoke_edge_function(self, function_name: str, payload: Optional[Dict[str, Any]] = None, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke a Supabase Edge Function.
        
        Args:
            function_name: Name of the function to invoke
            payload: Payload to send to the function
            access_token: Access token for authentication
            
        Returns:
            Dict[str, Any]: Response from the function
        """
        try:
            url = f"{self.url}/functions/v1/{function_name}"
            
            headers = self._get_auth_headers(access_token) if access_token else self._get_headers()
            
            response = requests.post(
                url,
                headers=headers,
                json=payload or {}
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'data': response.text}
        
        except Exception as e:
            logger.error(f"Error invoking Edge Function {function_name}: {e}")
            return {'error': str(e)}
    
    def list_edge_functions(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        List all available Supabase Edge Functions.
        
        Args:
            access_token: Access token for authentication
            
        Returns:
            Dict[str, Any]: List of available functions
        """
        try:
            url = f"{self.url}/functions/v1"
            
            headers = self._get_auth_headers(access_token) if access_token else self._get_headers()
            
            response = requests.get(
                url,
                headers=headers
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'data': response.text}
        
        except Exception as e:
            logger.error(f"Error listing Edge Functions: {e}")
            return {'error': str(e)}
    
    def invoke_postgres_function(self, schema: str, function_name: str, params: Optional[List[Any]] = None, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke a PostgreSQL function in Supabase.
        
        Args:
            schema: Schema containing the function
            function_name: Name of the function to invoke
            params: Parameters to pass to the function
            access_token: Access token for authentication
            
        Returns:
            Dict[str, Any]: Response from the function
        """
        try:
            url = f"{self.url}/rest/v1/rpc/{function_name}"
            
            headers = self._get_auth_headers(access_token) if access_token else self._get_headers()
            
            response = requests.post(
                url,
                headers=headers,
                json=params or []
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'data': response.text}
        
        except Exception as e:
            logger.error(f"Error invoking PostgreSQL function {schema}.{function_name}: {e}")
            return {'error': str(e)}
    
    def list_postgres_functions(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        List all available PostgreSQL functions in Supabase.
        
        Args:
            access_token: Access token for authentication
            
        Returns:
            Dict[str, Any]: List of available functions
        """
        try:
            sql = """
            SELECT 
                n.nspname as schema,
                p.proname as name,
                pg_get_function_arguments(p.oid) as arguments,
                t.typname as return_type
            FROM 
                pg_proc p
                LEFT JOIN pg_namespace n ON p.pronamespace = n.oid
                LEFT JOIN pg_type t ON p.prorettype = t.oid
            WHERE 
                n.nspname NOT IN ('pg_catalog', 'information_schema')
                AND p.prokind = 'f'
            ORDER BY 
                n.nspname, p.proname;
            """
            
            url = f"{self.url}/rest/v1/rpc/execute_sql"
            
            headers = self._get_auth_headers(access_token) if access_token else self._get_headers()
            
            response = requests.post(
                url,
                headers=headers,
                json={"sql": sql}
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'data': response.text}
        
        except Exception as e:
            logger.error(f"Error listing PostgreSQL functions: {e}")
            return {'error': str(e)}


class SupabaseFunctionManager:
    """
    Manager for Supabase functions.
    
    This class provides methods for managing Supabase functions,
    including invoking functions and handling responses.
    """
    
    def __init__(self, client: SupabaseFunctionsClient = None):
        """
        Initialize the Supabase function manager.
        
        Args:
            client: Supabase functions client
        """
        self.client = client or SupabaseFunctionsClient()
    
    def invoke_function(self, function_type: str, function_name: str, payload: Optional[Dict[str, Any]] = None, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke a Supabase function.
        
        Args:
            function_type: Type of function to invoke (edge or postgres)
            function_name: Name of the function to invoke
            payload: Payload to send to the function
            access_token: Access token for authentication
            
        Returns:
            Dict[str, Any]: Response from the function
        """
        if function_type == 'edge':
            return self.client.invoke_edge_function(function_name, payload, access_token)
        elif function_type == 'postgres':
            schema, func_name = function_name.split('.') if '.' in function_name else ('public', function_name)
            return self.client.invoke_postgres_function(schema, func_name, payload, access_token)
        else:
            return {'error': f"Invalid function type: {function_type}"}
    
    def list_functions(self, function_type: str, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        List all available Supabase functions.
        
        Args:
            function_type: Type of functions to list (edge or postgres)
            access_token: Access token for authentication
            
        Returns:
            Dict[str, Any]: List of available functions
        """
        if function_type == 'edge':
            return self.client.list_edge_functions(access_token)
        elif function_type == 'postgres':
            return self.client.list_postgres_functions(access_token)
        else:
            return {'error': f"Invalid function type: {function_type}"}


supabase_functions_client = SupabaseFunctionsClient()

supabase_function_manager = SupabaseFunctionManager(supabase_functions_client)
