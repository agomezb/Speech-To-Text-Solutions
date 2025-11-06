"""
Speech-to-Text Solution
Reads audio files from a directory and transcribes them using cloud speech services.
Results are saved to a CSV file.
"""

import os
import typer
from dotenv import load_dotenv
from providers import ProviderFactory

# Load environment variables from .env file
load_dotenv()

app = typer.Typer()


@app.command()
def main(
    audio_dir: str = typer.Option(
        None,
        "--audio-dir",
        "-a",
        help="Directory containing audio files"
    ),
    output_csv: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output CSV file path"
    ),
    language: str = typer.Option(
        None,
        "--language",
        "-l",
        help="Speech recognition language (e.g., 'en-US', 'es-ES')"
    ),
    provider: str = typer.Option(
        "azure",
        "--provider",
        "-p",
        help="Speech-to-text provider (azure, amazon, google)"
    )
):
    """
    Transcribe audio files to text using cloud speech services.
    
    Currently supported providers: azure (amazon and google coming soon)
    """
    # Load from environment variables or use defaults
    AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
    AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', 'eastus')
    AZURE_SPEECH_LANGUAGE = language or os.getenv('AZURE_SPEECH_LANGUAGE', 'en-US')
    AZURE_SPEECH_ENDPOINT = os.getenv('AZURE_SPEECH_ENDPOINT')
    
    if not AZURE_SPEECH_KEY:
        typer.secho(
            "Error: AZURE_SPEECH_KEY not set in .env file",
            fg=typer.colors.RED,
            bold=True
        )
        raise typer.Exit(1)
    
    # Paths
    audio_directory = audio_dir or os.getenv('AUDIO_DIR', './audio')
    output_file = output_csv or os.getenv('OUTPUT_CSV', './transcriptions.csv')
    
    try:
        # Create provider instance using factory
        stt = ProviderFactory.create_provider(
            provider=provider,
            subscription_key=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION,
            language=AZURE_SPEECH_LANGUAGE,
            endpoint=AZURE_SPEECH_ENDPOINT
        )
        
        typer.secho(
            f"Using provider: {provider.upper()}",
            fg=typer.colors.BLUE,
            bold=True
        )
        
        stt.transcribe_directory(
            audio_dir=audio_directory,
            output_csv=output_file
        )
        
        typer.secho(
            f"\n✓ Transcription complete!",
            fg=typer.colors.GREEN,
            bold=True
        )
    except NotImplementedError as e:
        typer.secho(
            f"Provider not available: {str(e)}",
            fg=typer.colors.YELLOW,
            bold=True
        )
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(
            f"Error: {str(e)}",
            fg=typer.colors.RED,
            bold=True
        )
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
