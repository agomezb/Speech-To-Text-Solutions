"""
Custom Service Speech-to-Text Provider
Handles speech-to-text transcription using a custom local/remote service.
"""

import os
import time
import requests
from typing import Dict
from .base_provider import SpeechToTextProvider


class CustomServiceProvider(SpeechToTextProvider):
    """Handles speech-to-text transcription using a custom HTTP service."""
    
    def __init__(self, service_uri: str, language: str = "en-US"):
        """
        Initialize Custom Service provider.
        
        Args:
            service_uri: Base URI of the transcription service (e.g., 'http://0.0.0.0:8000')
            language: Speech recognition language (default: 'en-US')
        """
        self.service_uri = service_uri.rstrip('/')
        self.language = language
        self.transcribe_endpoint = f"{self.service_uri}/transcribe"
        
        # Verify service is available
        try:
            health_response = requests.get(self.service_uri, timeout=5)
            health_response.raise_for_status()
            print(f"✓ Connected to custom service at {self.service_uri}")
        except Exception as e:
            print(f"Warning: Could not connect to service at {self.service_uri}: {e}")
    
    def transcribe_file(self, audio_file_path: str) -> Dict[str, str]:
        """
        Transcribe a single audio file using the custom service.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary with filename, text, and status
        """
        filename = os.path.basename(audio_file_path)
        
        try:
            print(f"Transcribing: {filename}")
            
            # Track transcription time
            start_time = time.time()
            
            # Open and send the audio file
            with open(audio_file_path, 'rb') as audio_file:
                files = {'file': (filename, audio_file)}
                
                # Send POST request to transcription endpoint
                response = requests.post(
                    self.transcribe_endpoint,
                    files=files,
                    timeout=300  # 5 minutes timeout for large files
                )
                
                # Check response status
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                
                # Calculate transcription time
                transcription_time = time.time() - start_time
                print(f"✓ Custom service transcription time: {transcription_time:.1f}s")
                
                # Extract text from response
                # Assuming the API returns {"text": "transcribed text", ...}
                text = result.get('text', '')
                
                return {
                    "filename": filename,
                    "text": text,
                    "status": "success",
                    "transcription_time": f"{transcription_time:.2f}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "filename": filename,
                "text": "",
                "status": "error: request timeout",
                "transcription_time": ""
            }
        except requests.exceptions.ConnectionError:
            return {
                "filename": filename,
                "text": "",
                "status": f"error: cannot connect to service at {self.service_uri}",
                "transcription_time": ""
            }
        except requests.exceptions.HTTPError as e:
            return {
                "filename": filename,
                "text": "",
                "status": f"error: HTTP {e.response.status_code}",
                "transcription_time": ""
            }
        except Exception as e:
            return {
                "filename": filename,
                "text": "",
                "status": f"exception: {str(e)}",
                "transcription_time": ""
            }
