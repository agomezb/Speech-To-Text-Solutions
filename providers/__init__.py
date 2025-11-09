"""Speech-to-Text Providers module."""

from .base_provider import SpeechToTextProvider
from .azure_provider import AzureSpeechToText
from .amazon_provider import AmazonTranscribe
from .custom_provider import CustomServiceProvider
from .provider_factory import ProviderFactory

__all__ = ['SpeechToTextProvider', 'AzureSpeechToText', 'AmazonTranscribe', 'CustomServiceProvider', 'ProviderFactory']
