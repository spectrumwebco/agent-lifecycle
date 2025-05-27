"""
Supabase integration for Django.
"""

import os
import logging
from django.conf import settings
from supabase import create_client, Client
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    Client for interacting with Supabase.
    """
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase URL. If not provided, will use settings.SUPABASE_URL.
            key: Supabase key. If not provided, will use settings.SUPABASE_KEY.
        """
        self.url = url or getattr(settings, 'SUPABASE_URL', os.environ.get('SUPABASE_URL'))
        self.key = key or getattr(settings, 'SUPABASE_KEY', os.environ.get('SUPABASE_KEY'))
        
        if not self.url or not self.key:
            logger.warning("Supabase URL or key not provided. Using mock client.")
            self.client = None
        else:
            self.client = create_client(self.url, self.key)
    
    def get_client(self) -> Optional[Client]:
        """
        Get Supabase client.
        
        Returns:
            Supabase client or None if not initialized.
        """
        return self.client
    
    def query_table(self, table_name: str, query_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query a Supabase table.
        
        Args:
            table_name: Name of the table to query.
            query_params: Query parameters.
        
        Returns:
            List of records.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning empty list.")
            return []
        
        query = self.client.table(table_name).select("*")
        
        if query_params:
            if 'filter' in query_params:
                for filter_key, filter_value in query_params['filter'].items():
                    query = query.filter(filter_key, 'eq', filter_value)
            
            if 'order' in query_params:
                for order_key, order_dir in query_params['order'].items():
                    query = query.order(order_key, desc=(order_dir.lower() == 'desc'))
            
            if 'limit' in query_params:
                query = query.limit(query_params['limit'])
            
            if 'offset' in query_params:
                query = query.offset(query_params['offset'])
        
        response = query.execute()
        
        if hasattr(response, 'data'):
            return response.data
        
        return []
    
    def insert_record(self, table_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a record into a Supabase table.
        
        Args:
            table_name: Name of the table to insert into.
            record: Record to insert.
        
        Returns:
            Inserted record.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning empty dict.")
            return {}
        
        response = self.client.table(table_name).insert(record).execute()
        
        if hasattr(response, 'data') and response.data:
            return response.data[0]
        
        return {}
    
    def update_record(self, table_name: str, record_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a record in a Supabase table.
        
        Args:
            table_name: Name of the table to update.
            record_id: ID of the record to update.
            record: Record data to update.
        
        Returns:
            Updated record.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning empty dict.")
            return {}
        
        response = self.client.table(table_name).update(record).eq('id', record_id).execute()
        
        if hasattr(response, 'data') and response.data:
            return response.data[0]
        
        return {}
    
    def delete_record(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from a Supabase table.
        
        Args:
            table_name: Name of the table to delete from.
            record_id: ID of the record to delete.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning False.")
            return False
        
        response = self.client.table(table_name).delete().eq('id', record_id).execute()
        
        if hasattr(response, 'data'):
            return True
        
        return False
    
    def execute_rpc(self, function_name: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute a Supabase RPC function.
        
        Args:
            function_name: Name of the function to execute.
            params: Function parameters.
        
        Returns:
            Function result.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning None.")
            return None
        
        response = self.client.rpc(function_name, params or {}).execute()
        
        if hasattr(response, 'data'):
            return response.data
        
        return None
    
    def get_auth_client(self):
        """
        Get Supabase auth client.
        
        Returns:
            Supabase auth client or None if not initialized.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning None.")
            return None
        
        return self.client.auth
    
    def get_storage_client(self):
        """
        Get Supabase storage client.
        
        Returns:
            Supabase storage client or None if not initialized.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning None.")
            return None
        
        return self.client.storage
    
    def get_functions_client(self):
        """
        Get Supabase functions client.
        
        Returns:
            Supabase functions client or None if not initialized.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning None.")
            return None
        
        return self.client.functions
