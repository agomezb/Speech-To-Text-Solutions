"""
Provider Factory
Creates speech-to-text provider instances based on the provider name.
"""

from typing import Optional
from .base_provider import SpeechToTextProvider
from .azure_provider import AzureSpeechToText
from .amazon_provider import AmazonTranscribe


class ProviderFactory:
    """Factory for creating speech-to-text provider instances."""
    
    @staticmethod
    def create_provider(
        provider: str,
        subscription_key: str = None,
        region: str = None,
        language: str = "en-US",
        endpoint: Optional[str] = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ) -> SpeechToTextProvider:
        """
        Create a speech-to-text provider instance.
        
        Args:
            provider: Provider name ('azure', 'amazon', 'google')
            subscription_key: API/subscription key (Azure)
            region: Service region
            language: Recognition language
            endpoint: Optional custom endpoint (Azure)
            aws_access_key_id: AWS access key (Amazon)
            aws_secret_access_key: AWS secret key (Amazon)
            
        Returns:
            SpeechToTextProvider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()
        
        if provider == "azure":
            if not subscription_key:
                raise ValueError("subscription_key is required for Azure provider")
            return AzureSpeechToText(
                subscription_key=subscription_key,
                region=region or "eastus",
                language=language,
                endpoint=endpoint
            )
        elif provider == "amazon":
            if not aws_access_key_id or not aws_secret_access_key:
                raise ValueError("aws_access_key_id and aws_secret_access_key are required for Amazon provider")
            return AmazonTranscribe(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region=region or "us-east-1",
                language=language
            )
        elif provider == "google":
            raise NotImplementedError("Google provider is not yet implemented")
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: azure, amazon (coming soon), google (coming soon)"
            )
