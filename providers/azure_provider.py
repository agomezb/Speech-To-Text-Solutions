"""
Azure Speech-to-Text Service
Handles speech-to-text transcription using Azure AI Services.
"""

import os
import time
from typing import Dict, Optional
import azure.cognitiveservices.speech as speechsdk
from .base_provider import SpeechToTextProvider


class AzureSpeechToText(SpeechToTextProvider):
    """Handles speech-to-text transcription using Azure Cognitive Services."""
    
    def __init__(
        self, 
        subscription_key: str, 
        region: str, 
        language: str = "en-US",
        endpoint: Optional[str] = None
    ):
        """
        Initialize Azure Speech service.
        
        Args:
            subscription_key: Azure Speech service subscription key
            region: Azure region (e.g., 'eastus', 'westeurope')
            language: Speech recognition language (default: 'en-US')
            endpoint: Optional custom endpoint URL (for custom models or containers)
        """
        super().__init__()
        self.provider_name = "azure"
        self.subscription_key = subscription_key
        self.region = region
        
        # Initialize SpeechConfig with endpoint if provided, otherwise use region
        if endpoint:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=subscription_key,
                endpoint=endpoint
            )
        else:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=subscription_key,
                region=region
            )
        
        # Set language for speech recognition
        self.speech_config.speech_recognition_language = language
        
        # Configure silence timeout for better results (Microsoft recommendation)
        # Segmentation silence timeout: 500ms default, adjust if needed
        self.speech_config.set_property(
            speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, 
            "1000"
        )
    
    def transcribe_file(self, audio_file_path: str) -> Dict[str, str]:
        """
        Transcribe a single audio file.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary with filename, text, and status
        """
        filename = os.path.basename(audio_file_path)
        
        try:
            audio_config = speechsdk.AudioConfig(filename=audio_file_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            print(f"Transcribing: {filename}")
            
            # Track transcription time
            start_time = time.time()
            result = speech_recognizer.recognize_once()
            transcription_time = time.time() - start_time
            
            print(f"✓ Azure transcription time: {transcription_time:.1f}s")
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {
                    "filename": filename,
                    "text": result.text,
                    "status": "success",
                    "transcription_time": f"{transcription_time:.2f}"
                }
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return {
                    "filename": filename,
                    "text": "",
                    "status": "no_speech_detected",
                    "transcription_time": f"{transcription_time:.2f}"
                }
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = speechsdk.CancellationDetails.FromResult(result)
                error_details = f"Reason={cancellation.reason}"
                
                # Include detailed error information (Microsoft recommendation)
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    error_details += f", ErrorCode={cancellation.error_code}"
                    if cancellation.error_details:
                        error_details += f", Details={cancellation.error_details}"
                
                return {
                    "filename": filename,
                    "text": "",
                    "status": f"canceled: {error_details}",
                    "transcription_time": f"{transcription_time:.2f}"
                }
            else:
                return {
                    "filename": filename,
                    "text": "",
                    "status": f"unknown_result: {result.reason}",
                    "transcription_time": f"{transcription_time:.2f}"
                }
                
        except Exception as e:
            return {
                "filename": filename,
                "text": "",
                "status": f"exception: {str(e)}",
                "transcription_time": ""
            }
