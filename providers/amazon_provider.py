"""
Amazon Transcribe Speech-to-Text Service
Handles speech-to-text transcription using AWS Transcribe.
"""

import os
import time
import uuid
import boto3
from typing import Dict
from .base_provider import SpeechToTextProvider


class AmazonTranscribe(SpeechToTextProvider):
    """Handles speech-to-text transcription using Amazon Transcribe."""
    
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str = "us-east-1",
        language: str = "en-US"
    ):
        """
        Initialize Amazon Transcribe service.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region (e.g., 'us-east-1', 'eu-west-1')
            language: Speech recognition language (default: 'en-US')
        """
        self.region = region
        self.language = language
        
        # Initialize boto3 clients
        self.transcribe_client = boto3.client(
            'transcribe',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        
        # Generate unique bucket name for temporary storage
        # Use UUID to ensure global uniqueness across all AWS accounts
        unique_id = str(uuid.uuid4())[:8]
        self.bucket_name = f"transcribe-temp-{unique_id}"
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create S3 bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Using existing bucket: {self.bucket_name}")
        except Exception as e:
            # Check if it's a 404 (bucket doesn't exist) or 403 (no permission)
            error_code = e.response.get('Error', {}).get('Code', '') if hasattr(e, 'response') else ''
            
            if error_code == '404' or 'NoSuchBucket' in str(e) or 'Not Found' in str(e):
                # Bucket doesn't exist, create it
                print(f"Creating bucket: {self.bucket_name}")
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    print(f"✓ Bucket created successfully: {self.bucket_name}")
                except Exception as create_error:
                    raise Exception(
                        f"Failed to create S3 bucket '{self.bucket_name}': {str(create_error)}. "
                        f"Please check your AWS permissions (s3:CreateBucket, s3:PutObject)"
                    )
            else:
                # Other error (permission denied, etc.)
                raise Exception(
                    f"Failed to access S3 bucket '{self.bucket_name}': {str(e)}. "
                    f"Please check your AWS credentials and permissions."
                )
    
    def transcribe_file(self, audio_file_path: str) -> Dict[str, str]:
        """
        Transcribe a single audio file using Amazon Transcribe.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary with filename, text, and status
        """
        filename = os.path.basename(audio_file_path)
        job_name = f"transcribe-{int(time.time())}-{filename.replace('.', '-')}"
        s3_key = f"audio/{filename}"
        
        try:
            # Upload file to S3
            print(f"Uploading: {filename}")
            self.s3_client.upload_file(audio_file_path, self.bucket_name, s3_key)
            
            # Start transcription job
            print(f"Transcribing: {filename}")
            media_uri = f"s3://{self.bucket_name}/{s3_key}"
            
            self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': media_uri},
                MediaFormat=filename.split('.')[-1],
                LanguageCode=self.language
            )
            
            # Wait for job to complete
            while True:
                response = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status in ['COMPLETED', 'FAILED']:
                    break
                time.sleep(2)
            
            # Clean up S3 file
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            # Get results
            if status == 'COMPLETED':
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                # Download transcript using requests library (more reliable than urllib)
                import json
                import urllib.request
                import ssl
                
                # Create SSL context that doesn't verify certificates (for development)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                with urllib.request.urlopen(transcript_uri, context=ssl_context) as resp:
                    transcript_data = json.loads(resp.read())
                
                text = transcript_data['results']['transcripts'][0]['transcript']
                
                # Clean up job
                self.transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                
                return {
                    "filename": filename,
                    "text": text,
                    "status": "success"
                }
            else:
                failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown')
                
                # Clean up failed job
                self.transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                
                return {
                    "filename": filename,
                    "text": "",
                    "status": f"failed: {failure_reason}"
                }
                
        except Exception as e:
            # Clean up on error
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                self.transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
            except:
                pass
            
            return {
                "filename": filename,
                "text": "",
                "status": f"exception: {str(e)}"
            }
