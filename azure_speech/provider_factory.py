"""
Provider Factory
Creates speech-to-text provider instances based on the provider name.
"""

from typing import Optional
from .base_provider import SpeechToTextProvider
from .speech_to_text import AzureSpeechToText


class ProviderFactory:
    """Factory for creating speech-to-text provider instances."""
    
    @staticmethod
    def create_provider(
        provider: str,
        subscription_key: str,
        region: str,
        language: str = "en-US",
        endpoint: Optional[str] = None
    ) -> SpeechToTextProvider:
        """
        Create a speech-to-text provider instance.
        
        Args:
            provider: Provider name ('azure', 'amazon', 'google')
            subscription_key: API/subscription key
            region: Service region
            language: Recognition language
            endpoint: Optional custom endpoint
            
        Returns:
            SpeechToTextProvider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()
        
        if provider == "azure":
            return AzureSpeechToText(
                subscription_key=subscription_key,
                region=region,
                language=language,
                endpoint=endpoint
            )
        elif provider == "amazon":
            raise NotImplementedError("Amazon provider is not yet implemented")
        elif provider == "google":
            raise NotImplementedError("Google provider is not yet implemented")
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: azure, amazon (coming soon), google (coming soon)"
            )
