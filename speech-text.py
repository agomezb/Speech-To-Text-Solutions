"""
Speech-to-Text Solution
Reads audio files from a directory and transcribes them using cloud speech services.
Results are saved to a CSV file.
"""

import typer
from providers import ProviderFactory
from config import ProviderConfig, AzureConfig, AmazonConfig, GoogleConfig, CustomServiceConfig

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
        help="Speech-to-text provider (azure, amazon, google, custom_service)"
    )
):
    """
    Transcribe audio files to text using cloud speech services.
    
    Supported providers:
    - azure: Requires AZURE_SPEECH_KEY and AZURE_SPEECH_REGION
    - amazon: Requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    - google: Requires GOOGLE_CLOUD_PROJECT (optional: GOOGLE_APPLICATION_CREDENTIALS for JSON auth)
    - custom_service: Requires CUSTOM_SERVICE_URI (default: http://0.0.0.0:8000)
    """
    provider = provider.lower()
    
    # Get common settings
    common_settings = ProviderConfig.get_common_settings(language)
    audio_directory = audio_dir or common_settings['audio_dir']
    output_file = output_csv or common_settings['output_csv']
    lang = common_settings['language']
    
    # Validate and get provider configuration
    config_classes = {
        "azure": AzureConfig,
        "amazon": AmazonConfig,
        "google": GoogleConfig,
        "custom_service": CustomServiceConfig
    }
    
    if provider not in config_classes:
        typer.secho(
            f"Error: Unknown provider '{provider}'. Use: azure, amazon, google, or custom_service",
            fg=typer.colors.RED,
            bold=True
        )
        raise typer.Exit(1)
    
    # Validate provider configuration
    config_class = config_classes[provider]
    is_valid, error_msg = config_class.validate()
    if not is_valid:
        typer.secho(f"Error: {error_msg}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(1)
    
    # Get configuration
    config = config_class.from_env()
    
    try:
        # Create provider instance using factory
        stt = ProviderFactory.create_provider(
            provider=provider,
            config=config,
            language=lang
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
