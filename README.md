# Speech-to-Text Solution

Simple solution to transcribe audio files using cloud speech services (Azure, Amazon, Google).

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Edit `.env` and set your credentials:
   
   **For Azure:**
   ```bash
   AZURE_SPEECH_KEY=your-azure-speech-key
   AZURE_SPEECH_REGION=southcentralus
   AZURE_SPEECH_LANGUAGE=es-ES
   ```
   
   **For Amazon:**
   ```bash
   AWS_ACCESS_KEY_ID=your-aws-access-key-id
   AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
   AWS_REGION=us-east-1
   AWS_LANGUAGE_CODE=en-US
   ```
   
   **For Custom Service:**
   ```bash
   CUSTOM_SERVICE_URI=http://0.0.0.0:8000
   ```

## Usage

### Basic usage (uses .env configuration with Azure):
```bash
python speech-text.py
```

### With command-line options:
```bash
# Specify audio directory
python speech-text.py --audio-dir /path/to/audio

# Specify output file
python speech-text.py --output results.csv

# Change language
python speech-text.py --language es-ES

# Choose provider (Azure, Amazon, or Custom Service)
python speech-text.py --provider azure
python speech-text.py --provider amazon
python speech-text.py --provider custom_service

# Combine options
python speech-text.py -a ./recordings -o output.csv -l en-US -p azure
```

### Get help:
```bash
python speech-text.py --help
```

### Supported Providers:
- **Azure** ✅ - Azure Cognitive Services Speech
- **Amazon** ✅ - Amazon Transcribe with S3
- **Custom Service** ✅ - Local or custom HTTP transcription service
- **Google** 🔜 - Coming soon

The script will:
- Load configuration from `.env` file (can be overridden with CLI options)
- Use the specified provider (default: Azure)
- Look for audio files in the specified directory
- Save transcription results to CSV file

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

## Getting Credentials

### Azure
1. Go to [Azure Portal](https://portal.azure.com)
2. Create a Speech service resource
3. Copy the Key and Region from the resource

### Amazon
1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Create an IAM user with Transcribe and S3 permissions
3. Generate access keys
4. Copy Access Key ID and Secret Access Key

### Custom Service
1. Run your local transcription service (e.g., on http://0.0.0.0:8000)
2. Service must implement POST /transcribe endpoint accepting multipart/form-data file upload
3. Service must return JSON response with "text" field
4. Set CUSTOM_SERVICE_URI in .env to your service URL

## Architecture

The solution follows SOLID principles with a simple, extensible architecture:

```
providers/
├── base_provider.py      # Abstract base class (interface)
├── azure_provider.py     # Azure implementation
├── amazon_provider.py    # Amazon implementation
├── provider_factory.py   # Factory pattern for provider creation
└── __init__.py
```

- **SpeechToTextProvider**: Abstract base class defining the interface
- **AzureSpeechToText**: Concrete implementation for Azure
- **AmazonTranscribe**: Concrete implementation for Amazon
- **ProviderFactory**: Factory to create provider instances

This design makes it easy to add new providers (Google) without modifying existing code.
