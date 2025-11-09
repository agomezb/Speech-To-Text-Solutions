"""
Configuration management for speech-to-text providers.
Handles loading and validation of provider-specific configurations.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ProviderConfig:
    """Base configuration class for all providers."""
    
    @staticmethod
    def get_common_settings(language: Optional[str] = None) -> Dict[str, str]:
        """Get common settings across all providers."""
        return {
            'language': language or os.getenv('AZURE_SPEECH_LANGUAGE', 'en-US'),
            'audio_dir': os.getenv('AUDIO_DIR', './audio'),
            'output_csv': os.getenv('OUTPUT_CSV', './transcriptions.csv')
        }


class AzureConfig:
    """Azure Speech Service configuration."""
    
    @staticmethod
    def from_env() -> Dict[str, Optional[str]]:
        """Load Azure configuration from environment variables."""
        return {
            'subscription_key': os.getenv('AZURE_SPEECH_KEY'),
            'region': os.getenv('AZURE_SPEECH_REGION', 'eastus'),
            'endpoint': os.getenv('AZURE_SPEECH_ENDPOINT')
        }
    
    @staticmethod
    def validate() -> tuple[bool, Optional[str]]:
        """Validate Azure configuration."""
        config = AzureConfig.from_env()
        if not config['subscription_key']:
            return False, "AZURE_SPEECH_KEY not set in .env file"
        return True, None


class AmazonConfig:
    """Amazon Transcribe configuration."""
    
    @staticmethod
    def from_env() -> Dict[str, Optional[str]]:
        """Load Amazon configuration from environment variables."""
        return {
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'region': os.getenv('AWS_REGION', 'us-east-1')
        }
    
    @staticmethod
    def validate() -> tuple[bool, Optional[str]]:
        """Validate Amazon configuration."""
        config = AmazonConfig.from_env()
        if not config['aws_access_key_id'] or not config['aws_secret_access_key']:
            return False, "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not set in .env file"
        return True, None


class GoogleConfig:
    """Google Cloud Speech configuration."""
    
    @staticmethod
    def from_env() -> Dict[str, Optional[str]]:
        """Load Google configuration from environment variables."""
        return {
            'project_id': os.getenv('GOOGLE_CLOUD_PROJECT'),
            'location': os.getenv('GOOGLE_CLOUD_LOCATION', 'global'),
            'credentials_file': os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        }
    
    @staticmethod
    def validate() -> tuple[bool, Optional[str]]:
        """Validate Google configuration."""
        config = GoogleConfig.from_env()
        if not config['project_id']:
            return False, "GOOGLE_CLOUD_PROJECT not set in .env file"
        return True, None
        return True, None


class CustomServiceConfig:
    """Custom Service configuration."""
    
    @staticmethod
    def from_env() -> Dict[str, Optional[str]]:
        """Load Custom Service configuration from environment variables."""
        return {
            'service_uri': os.getenv('CUSTOM_SERVICE_URI', 'http://0.0.0.0:8000')
        }
    
    @staticmethod
    def validate() -> tuple[bool, Optional[str]]:
        """Validate Custom Service configuration."""
        config = CustomServiceConfig.from_env()
        if not config['service_uri']:
            return False, "CUSTOM_SERVICE_URI not set in .env file"
        return True, None
