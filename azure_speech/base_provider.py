"""
Base Speech-to-Text Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from pathlib import Path
import csv


class SpeechToTextProvider(ABC):
    """Abstract base class for speech-to-text providers."""
    
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
