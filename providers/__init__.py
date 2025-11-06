"""Speech-to-Text Providers module."""

from .base_provider import SpeechToTextProvider
from .azure_provider import AzureSpeechToText
from .provider_factory import ProviderFactory

__all__ = ['SpeechToTextProvider', 'AzureSpeechToText', 'ProviderFactory']
