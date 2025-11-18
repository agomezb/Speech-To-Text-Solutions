"""
Base Speech-to-Text Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from pathlib import Path
import csv
import os


class SpeechToTextProvider(ABC):
    """Abstract base class for speech-to-text providers."""
    
    def __init__(self):
        """Initialize base provider with a provider name."""
        self.provider_name = "unknown"
    
    @abstractmethod
    def transcribe_file(self, audio_file_path: str) -> Dict[str, str]:
        """
        Transcribe a single audio file.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary with filename, text, and status
        """
        pass
    
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
            # Add provider name to result
            result['provider'] = self.provider_name
            results.append(result)
        
        # Check if we're appending or creating new file
        file_exists = os.path.exists(output_csv)
        
        # Save to CSV
        self._save_to_csv(results, output_csv)
        
        if file_exists:
            print(f"\nResults appended to: {output_csv}")
        else:
            print(f"\nResults saved to: {output_csv}")
    
    def _save_to_csv(self, results: List[Dict[str, str]], output_file: str) -> None:
        """
        Save transcription results to CSV.
        If the file exists, append results to it. Otherwise, create a new file.
        
        Args:
            results: List of transcription results
            output_file: Output CSV file path
        """
        if not results:
            return
        
        # Collect all unique fields from all results
        fieldnames = []
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        # Standard fields first (provider added as first column after filename)
        standard_fields = ['filename', 'provider', 'text', 'status', 'transcription_time']
        fieldnames = [f for f in standard_fields if f in all_keys]
        
        # Add any additional fields
        additional_fields = sorted(all_keys - set(standard_fields))
        fieldnames.extend(additional_fields)
        
        # Check if file exists to determine if we should append or create new
        file_exists = os.path.exists(output_file)
        
        # If file exists, verify it has content and read the existing fieldnames
        if file_exists:
            try:
                with open(output_file, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    existing_fieldnames = reader.fieldnames
                    if existing_fieldnames:
                        # Use existing fieldnames to maintain consistency
                        # Add any new fields that don't exist yet
                        for field in fieldnames:
                            if field not in existing_fieldnames:
                                existing_fieldnames.append(field)
                        fieldnames = existing_fieldnames
            except (IOError, csv.Error):
                # If there's an error reading the file, treat it as new
                file_exists = False
        
        # Open file in append mode if it exists, write mode if new
        mode = 'a' if file_exists else 'w'
        
        with open(output_file, mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            
            # Only write header if creating a new file
            if not file_exists:
                writer.writeheader()
            
            # Write all results
            for result in results:
                writer.writerow(result)
