"""
Azure Speech-to-Text Solution
Reads audio files from a directory and transcribes them using Azure Cognitive Services.
Results are saved to a CSV file.
"""

import os
from azure_speech import AzureSpeechToText


def main():
    """Main entry point."""
    # Configuration - load from environment variables
    AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
    AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', 'eastus')
    AZURE_SPEECH_LANGUAGE = os.getenv('AZURE_SPEECH_LANGUAGE', 'en-US')
    AZURE_SPEECH_ENDPOINT = os.getenv('AZURE_SPEECH_ENDPOINT')  # Optional
    
    if not AZURE_SPEECH_KEY:
        raise ValueError(
            "AZURE_SPEECH_KEY environment variable not set. "
            "Set it with: export AZURE_SPEECH_KEY='your-key'"
        )
    
    # Paths
    audio_directory = os.getenv('AUDIO_DIR', './audio')
    output_csv = os.getenv('OUTPUT_CSV', './transcriptions.csv')
    
    # Initialize and run
    stt = AzureSpeechToText(
        subscription_key=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
        language=AZURE_SPEECH_LANGUAGE,
        endpoint=AZURE_SPEECH_ENDPOINT
    )
    
    stt.transcribe_directory(
        audio_dir=audio_directory,
        output_csv=output_csv
    )


if __name__ == "__main__":
    main()
