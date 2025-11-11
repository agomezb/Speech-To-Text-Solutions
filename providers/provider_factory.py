"""
Provider Factory
Creates speech-to-text provider instances based on the provider name.
"""

from typing import Dict, Any
from .base_provider import SpeechToTextProvider
from .azure_provider import AzureSpeechToText
from .amazon_provider import AmazonTranscribe
from .custom_provider import CustomServiceProvider
from .google_provider import GoogleSpeechToText


class ProviderFactory:
    """Factory for creating speech-to-text provider instances."""
    
    @staticmethod
    def create_provider(
        provider: str,
        config: Dict[str, Any],
        language: str = "en-US"
    ) -> SpeechToTextProvider:
        """
        Create a speech-to-text provider instance.
        
        Args:
            provider: Provider name ('azure', 'amazon', 'google', 'custom_service')
            config: Configuration dictionary from provider config class
            language: Recognition language (default: 'en-US')
            
        Returns:
            SpeechToTextProvider instance
            
        Raises:
            ValueError: If provider is not supported or required config is missing
        """
        provider = provider.lower()
        
        if provider == "azure":
            if not config.get('subscription_key'):
                raise ValueError("subscription_key is required for Azure provider")
            return AzureSpeechToText(
                subscription_key=config['subscription_key'],
                region=config.get('region', 'eastus'),
                language=language,
                endpoint=config.get('endpoint')
            )
        elif provider == "amazon":
            if not config.get('aws_access_key_id') or not config.get('aws_secret_access_key'):
                raise ValueError("aws_access_key_id and aws_secret_access_key are required for Amazon provider")
            if not config.get('bucket_name'):
                raise ValueError("bucket_name is required for Amazon provider")
            return AmazonTranscribe(
                aws_access_key_id=config['aws_access_key_id'],
                aws_secret_access_key=config['aws_secret_access_key'],
                region=config.get('region', 'us-east-1'),
                language=language,
                bucket_name=config['bucket_name']
            )
        elif provider == "custom_service":
            if not config.get('service_uri'):
                raise ValueError("service_uri is required for Custom Service provider")
            return CustomServiceProvider(
                service_uri=config['service_uri'],
                language=language
            )
        elif provider == "google":
            if not config.get('project_id'):
                raise ValueError("project_id is required for Google provider")
            return GoogleSpeechToText(
                project_id=config['project_id'],
                location=config.get('location', 'global'),
                language=language,
                credentials_file=config.get('credentials_file')
            )
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: azure, amazon, google, custom_service"
            )

