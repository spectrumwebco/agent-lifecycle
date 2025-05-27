"""
Supabase storage integration for the python_agent app.

This module provides integration with Supabase storage,
enabling file storage capabilities with access control.
"""

import json
import logging
import os
import requests
from typing import Dict, List, Any, Optional, Union, BinaryIO
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)


class SupabaseStorageClient:
    """
    Client for interacting with Supabase storage.
    
    This client provides methods for storing, retrieving, and managing
    files in Supabase storage.
    """
    
    def __init__(self, url=None, api_key=None):
        """
        Initialize the Supabase storage client.
        
        Args:
            url: Supabase URL
            api_key: Supabase API key
        """
        supabase_config = getattr(settings, 'SUPABASE_CONFIG', {})
        
        self.url = url or supabase_config.get('url', '')
        self.api_key = api_key or supabase_config.get('api_key', '')
        
        if not self.url or not self.api_key:
            logger.warning("Supabase URL or API key not provided. Storage will not work.")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Supabase API requests.
        
        Returns:
            Dict[str, str]: Headers for Supabase API requests
        """
        return {
            'apikey': self.api_key,
            'Authorization': f"Bearer {self.api_key}"
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
    
    def list_buckets(self) -> Dict[str, Any]:
        """
        List all storage buckets.
        
        Returns:
            Dict[str, Any]: List of storage buckets
        """
        try:
            url = f"{self.url}/storage/v1/bucket"
            
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            return {'error': str(e)}
    
    def create_bucket(self, bucket_name: str, public: bool = False) -> Dict[str, Any]:
        """
        Create a new storage bucket.
        
        Args:
            bucket_name: Name of the bucket to create
            public: Whether the bucket should be public
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/storage/v1/bucket"
            
            payload = {
                'name': bucket_name,
                'public': public
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            return {'error': str(e)}
    
    def delete_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """
        Delete a storage bucket.
        
        Args:
            bucket_name: Name of the bucket to delete
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/storage/v1/bucket/{bucket_name}"
            
            response = requests.delete(
                url,
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error deleting bucket {bucket_name}: {e}")
            return {'error': str(e)}
    
    def list_files(self, bucket_name: str, path: str = '') -> Dict[str, Any]:
        """
        List files in a storage bucket.
        
        Args:
            bucket_name: Name of the bucket to list files from
            path: Path to list files from
            
        Returns:
            Dict[str, Any]: List of files
        """
        try:
            url = f"{self.url}/storage/v1/object/list/{bucket_name}"
            
            params = {
                'prefix': path
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=params
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error listing files in bucket {bucket_name}: {e}")
            return {'error': str(e)}
    
    def upload_file(self, bucket_name: str, path: str, file_data: Union[bytes, BinaryIO], content_type: str = None) -> Dict[str, Any]:
        """
        Upload a file to a storage bucket.
        
        Args:
            bucket_name: Name of the bucket to upload to
            path: Path to upload the file to
            file_data: File data to upload
            content_type: Content type of the file
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/storage/v1/object/{bucket_name}/{path}"
            
            headers = self._get_headers()
            
            if content_type:
                headers['Content-Type'] = content_type
            
            response = requests.post(
                url,
                headers=headers,
                data=file_data
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error uploading file to {bucket_name}/{path}: {e}")
            return {'error': str(e)}
    
    def download_file(self, bucket_name: str, path: str) -> bytes:
        """
        Download a file from a storage bucket.
        
        Args:
            bucket_name: Name of the bucket to download from
            path: Path to download the file from
            
        Returns:
            bytes: File data
        """
        try:
            url = f"{self.url}/storage/v1/object/{bucket_name}/{path}"
            
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error downloading file from {bucket_name}/{path}: {e}")
            return b''
    
    def delete_file(self, bucket_name: str, path: str) -> Dict[str, Any]:
        """
        Delete a file from a storage bucket.
        
        Args:
            bucket_name: Name of the bucket to delete from
            path: Path to delete the file from
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/storage/v1/object/{bucket_name}/{path}"
            
            response = requests.delete(
                url,
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            
            return {'status': 'success'}
        
        except Exception as e:
            logger.error(f"Error deleting file from {bucket_name}/{path}: {e}")
            return {'error': str(e)}
    
    def get_public_url(self, bucket_name: str, path: str) -> str:
        """
        Get the public URL for a file.
        
        Args:
            bucket_name: Name of the bucket containing the file
            path: Path to the file
            
        Returns:
            str: Public URL for the file
        """
        return f"{self.url}/storage/v1/object/public/{bucket_name}/{path}"
    
    def get_signed_url(self, bucket_name: str, path: str, expires_in: int = 60) -> Dict[str, Any]:
        """
        Get a signed URL for a file.
        
        Args:
            bucket_name: Name of the bucket containing the file
            path: Path to the file
            expires_in: Number of seconds until the URL expires
            
        Returns:
            Dict[str, Any]: Signed URL for the file
        """
        try:
            url = f"{self.url}/storage/v1/object/sign/{bucket_name}/{path}"
            
            params = {
                'expiresIn': expires_in
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=params
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error getting signed URL for {bucket_name}/{path}: {e}")
            return {'error': str(e)}
    
    def move_file(self, bucket_name: str, source_path: str, destination_path: str) -> Dict[str, Any]:
        """
        Move a file within a storage bucket.
        
        Args:
            bucket_name: Name of the bucket containing the file
            source_path: Path to the source file
            destination_path: Path to the destination file
            
        Returns:
            Dict[str, Any]: Response from Supabase
        """
        try:
            url = f"{self.url}/storage/v1/object/move"
            
            payload = {
                'bucketId': bucket_name,
                'sourceKey': source_path,
                'destinationKey': destination_path
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error moving file from {source_path} to {destination_path}: {e}")
            return {'error': str(e)}


@deconstructible
class SupabaseStorage(Storage):
    """
    Django storage backend for Supabase storage.
    
    This storage backend provides integration with Supabase storage,
    allowing Django to store files in Supabase.
    """
    
    def __init__(self, bucket_name=None, client=None):
        """
        Initialize the Supabase storage backend.
        
        Args:
            bucket_name: Name of the bucket to use
            client: Supabase storage client
        """
        supabase_config = getattr(settings, 'SUPABASE_CONFIG', {})
        
        self.bucket_name = bucket_name or supabase_config.get('storage_bucket', 'django')
        self.client = client or SupabaseStorageClient()
    
    def _open(self, name, mode='rb'):
        """
        Open a file from Supabase storage.
        
        Args:
            name: Name of the file to open
            mode: Mode to open the file in
            
        Returns:
            File: File object
        """
        if mode != 'rb':
            raise ValueError("Supabase storage only supports reading files in binary mode")
        
        file_data = self.client.download_file(self.bucket_name, name)
        
        return ContentFile(file_data)
    
    def _save(self, name, content):
        """
        Save a file to Supabase storage.
        
        Args:
            name: Name of the file to save
            content: File content to save
            
        Returns:
            str: Name of the saved file
        """
        content_type = getattr(content, 'content_type', None)
        
        if hasattr(content, 'chunks'):
            content_data = b''.join(chunk for chunk in content.chunks())
        else:
            content.seek(0)
            content_data = content.read()
        
        self.client.upload_file(self.bucket_name, name, content_data, content_type)
        
        return name
    
    def delete(self, name):
        """
        Delete a file from Supabase storage.
        
        Args:
            name: Name of the file to delete
        """
        self.client.delete_file(self.bucket_name, name)
    
    def exists(self, name):
        """
        Check if a file exists in Supabase storage.
        
        Args:
            name: Name of the file to check
            
        Returns:
            bool: True if the file exists, False otherwise
        """
        try:
            path_parts = name.rsplit('/', 1)
            
            if len(path_parts) > 1:
                prefix = path_parts[0] + '/'
                filename = path_parts[1]
            else:
                prefix = ''
                filename = name
            
            files = self.client.list_files(self.bucket_name, prefix)
            
            if 'error' in files:
                return False
            
            for file in files:
                if file['name'] == filename:
                    return True
            
            return False
        
        except Exception:
            return False
    
    def listdir(self, path):
        """
        List the contents of a directory in Supabase storage.
        
        Args:
            path: Path to list
            
        Returns:
            tuple: Tuple of (directories, files)
        """
        path = path.rstrip('/')
        
        if path:
            path = path + '/'
        
        files = self.client.list_files(self.bucket_name, path)
        
        if 'error' in files:
            return ([], [])
        
        directories = set()
        filenames = []
        
        for file in files:
            name = file['name']
            
            if '/' in name:
                directory = name.split('/', 1)[0]
                directories.add(directory)
            else:
                filenames.append(name)
        
        return (list(directories), filenames)
    
    def size(self, name):
        """
        Get the size of a file in Supabase storage.
        
        Args:
            name: Name of the file to get the size of
            
        Returns:
            int: Size of the file in bytes
        """
        try:
            path_parts = name.rsplit('/', 1)
            
            if len(path_parts) > 1:
                prefix = path_parts[0] + '/'
                filename = path_parts[1]
            else:
                prefix = ''
                filename = name
            
            files = self.client.list_files(self.bucket_name, prefix)
            
            if 'error' in files:
                return 0
            
            for file in files:
                if file['name'] == filename:
                    return file['metadata'].get('size', 0)
            
            return 0
        
        except Exception:
            return 0
    
    def url(self, name):
        """
        Get the URL for a file in Supabase storage.
        
        Args:
            name: Name of the file to get the URL for
            
        Returns:
            str: URL for the file
        """
        return self.client.get_public_url(self.bucket_name, name)
    
    def get_accessed_time(self, name):
        """
        Get the last accessed time of a file in Supabase storage.
        
        Args:
            name: Name of the file to get the accessed time of
            
        Returns:
            datetime: Last accessed time of the file
        """
        raise NotImplementedError("Supabase storage does not support getting accessed time")
    
    def get_created_time(self, name):
        """
        Get the created time of a file in Supabase storage.
        
        Args:
            name: Name of the file to get the created time of
            
        Returns:
            datetime: Created time of the file
        """
        raise NotImplementedError("Supabase storage does not support getting created time")
    
    def get_modified_time(self, name):
        """
        Get the last modified time of a file in Supabase storage.
        
        Args:
            name: Name of the file to get the modified time of
            
        Returns:
            datetime: Last modified time of the file
        """
        raise NotImplementedError("Supabase storage does not support getting modified time")


supabase_storage_client = SupabaseStorageClient()
