# Azure Speech-to-Text Solution

Simple solution to transcribe audio files using Azure Cognitive Services.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Azure credentials:
```bash
export AZURE_SPEECH_KEY='your-azure-speech-key'
export AZURE_SPEECH_REGION='your-region'  # e.g., eastus, westeurope
export AZURE_SPEECH_LANGUAGE='en-US'  # Optional, default: en-US
export AZURE_SPEECH_ENDPOINT='https://...'  # Optional, for custom models/endpoints
```

> **Note**: The `AZURE_SPEECH_ENDPOINT` is only needed if you're using:
> - Custom Speech models (custom endpoints)
> - Speech containers
> - Custom domains with AAD authentication
> 
> For standard Azure Speech Service, just use `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`.

## Usage

### Basic usage (using default paths):
```bash
python speech-text-azure.py
```

By default, it will:
- Look for audio files in `./audio` directory
- Save results to `./transcriptions.csv`

### Custom paths:
```bash
export AUDIO_DIR='/path/to/your/audio/files'
export OUTPUT_CSV='/path/to/output.csv'
python speech-text-azure.py
```

### Supported audio formats:
- .wav
- .mp3
- .ogg
- .flac

## Output

The script generates a CSV file with three columns:
- `filename`: Name of the audio file
- `text`: Transcribed text
- `status`: Status of the transcription (success, error, etc.)

## Getting Azure Credentials

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a Speech service resource
3. Copy the Key and Region from the resource
