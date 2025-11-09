"""Google Cloud Speech-to-Text provider implementation."""

import os
from typing import Optional
from google.cloud.speech_v2 import SpeechClient  # type: ignore
from google.cloud.speech_v2.types import cloud_speech  # type: ignore
from google.oauth2 import service_account  # type: ignore
from .base_provider import SpeechToTextProvider


class GoogleSpeechToText(SpeechToTextProvider):
    """Google Cloud Speech-to-Text implementation using v2 API."""
    
    def __init__(
        self, 
        project_id: str, 
        location: str = "global", 
        language: str = "en-US",
        credentials_file: Optional[str] = None
    ):
        """
        Initialize Google Speech-to-Text client.
        
        Args:
            project_id: Google Cloud project ID
            location: Location for processing (default: "global")
            language: Language code for transcription (default: "en-US")
            credentials_file: Path to service account JSON file (optional)
                If not provided, uses Application Default Credentials (ADC)
        """
        self.project_id = project_id
        self.location = location
        self.language = language
        
        # Initialize client with appropriate credentials
        if credentials_file and os.path.exists(credentials_file):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_file
            )
            self.client = SpeechClient(credentials=credentials)
        else:
            # Use Application Default Credentials (ADC)
            self.client = SpeechClient()
        
    def transcribe_file(self, audio_file: str) -> dict:
        """
        Transcribe an audio file using Google Cloud Speech-to-Text.
        
        Args:
            audio_file: Path to the audio file to transcribe
            
        Returns:
            Dictionary with 'text' and 'status' keys
        """
        try:
            # Read audio file
            with open(audio_file, "rb") as f:
                audio_content = f.read()
            
            # Configure recognition request
            config = cloud_speech.RecognitionConfig(
                auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
                language_codes=[self.language],
                model="long",
            )
            
            request = cloud_speech.RecognizeRequest(
                recognizer=f"projects/{self.project_id}/locations/{self.location}/recognizers/_",
                config=config,
                content=audio_content,
            )
            
            # Perform synchronous recognition
            response = self.client.recognize(request=request)
            
            # Extract transcription from response
            transcript = ""
            for result in response.results:
                if result.alternatives:
                    transcript += result.alternatives[0].transcript + " "
            
            filename = os.path.basename(audio_file)
            return {
                "filename": filename,
                "text": transcript.strip(),
                "status": "success"
            }
            
        except Exception as e:
            filename = os.path.basename(audio_file)
            return {
                "filename": filename,
                "text": "",
                "status": f"error: {str(e)}"
            }
