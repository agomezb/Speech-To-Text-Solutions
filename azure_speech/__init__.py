"""Azure Speech Services module."""

from .base_provider import SpeechToTextProvider
from .speech_to_text import AzureSpeechToText
from .provider_factory import ProviderFactory

__all__ = ['SpeechToTextProvider', 'AzureSpeechToText', 'ProviderFactory']
