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
    
    # Validate provider configuration
    if provider == "azure":
        is_valid, error_msg = AzureConfig.validate()
        if not is_valid:
            typer.secho(f"Error: {error_msg}", fg=typer.colors.RED, bold=True)
            raise typer.Exit(1)
        config = AzureConfig.from_env()
        
    elif provider == "amazon":
        is_valid, error_msg = AmazonConfig.validate()
        if not is_valid:
            typer.secho(f"Error: {error_msg}", fg=typer.colors.RED, bold=True)
            raise typer.Exit(1)
        config = AmazonConfig.from_env()
        
    elif provider == "google":
        is_valid, error_msg = GoogleConfig.validate()
        if not is_valid:
            typer.secho(f"Error: {error_msg}", fg=typer.colors.RED, bold=True)
            raise typer.Exit(1)
        config = GoogleConfig.from_env()
    
    elif provider == "custom_service":
        is_valid, error_msg = CustomServiceConfig.validate()
        if not is_valid:
            typer.secho(f"Error: {error_msg}", fg=typer.colors.RED, bold=True)
            raise typer.Exit(1)
        config = CustomServiceConfig.from_env()
        
    else:
        typer.secho(
            f"Error: Unknown provider '{provider}'. Use: azure, amazon, google, or custom_service",
            fg=typer.colors.RED,
            bold=True
        )
        raise typer.Exit(1)
    
    try:
        # Create provider instance using factory
        if provider == "azure":
            stt = ProviderFactory.create_provider(
                provider=provider,
                subscription_key=config['subscription_key'],
                region=config['region'],
                language=lang,
                endpoint=config['endpoint']
            )
        elif provider == "amazon":
            stt = ProviderFactory.create_provider(
                provider=provider,
                aws_access_key_id=config['aws_access_key_id'],
                aws_secret_access_key=config['aws_secret_access_key'],
                region=config['region'],
                language=lang
            )
        elif provider == "custom_service":
            stt = ProviderFactory.create_provider(
                provider=provider,
                custom_service_uri=config['service_uri']
            )
        elif provider == "google":
            stt = ProviderFactory.create_provider(
                provider=provider,
                project_id=config['project_id'],
                location=config['location'],
                language=lang,
                credentials_file=config['credentials_file']
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
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
