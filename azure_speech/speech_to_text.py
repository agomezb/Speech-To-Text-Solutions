"""
Azure Speech-to-Text Service
Handles speech-to-text transcription using Azure Cognitive Services.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Optional
import azure.cognitiveservices.speech as speechsdk

class AzureSpeechToText:
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
            "500"
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
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {
                    "filename": filename,
                    "text": result.text,
                    "status": "success"
                }
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return {
                    "filename": filename,
                    "text": "",
                    "status": "no_speech_detected"
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
                    "status": f"canceled: {error_details}"
                }
            else:
                return {
                    "filename": filename,
                    "text": "",
                    "status": f"unknown_result: {result.reason}"
                }
                
        except Exception as e:
            return {
                "filename": filename,
                "text": "",
                "status": f"exception: {str(e)}"
            }
    
    def transcribe_directory(
        self,
        audio_dir: str,
        output_csv: str,
        supported_extensions: tuple = ('.wav', '.mp3', '.ogg', '.flac')
    ) -> None:
        """
        Transcribe all audio files in a directory and save to CSV.
        
        Args:
            audio_dir: Directory containing audio files
            output_csv: Output CSV file path
            supported_extensions: Tuple of supported audio file extensions
        """
        audio_dir_path = Path(audio_dir)
        
        if not audio_dir_path.exists():
            raise ValueError(f"Directory not found: {audio_dir}")
        
        # Find all audio files
        audio_files = [
            str(f) for f in audio_dir_path.iterdir()
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        if not audio_files:
            print(f"No audio files found in {audio_dir}")
            return
        
        print(f"Found {len(audio_files)} audio files")
        
        # Transcribe all files
        results = []
        for audio_file in sorted(audio_files):
            result = self.transcribe_file(audio_file)
            results.append(result)
        
        # Save to CSV
        self._save_to_csv(results, output_csv)
        print(f"\nResults saved to: {output_csv}")
    
    def _save_to_csv(self, results: List[Dict[str, str]], output_file: str) -> None:
        """
        Save transcription results to CSV.
        
        Args:
            results: List of transcription results
            output_file: Output CSV file path
        """
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['filename', 'text', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
