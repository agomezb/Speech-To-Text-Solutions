"""
Amazon Transcribe Speech-to-Text Service
Handles speech-to-text transcription using AWS Transcribe.
"""

import os
import time
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
        language: str = "en-US",
        bucket_name: str = None
    ):
        """
        Initialize Amazon Transcribe service.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region (e.g., 'us-east-1', 'eu-west-1')
            language: Speech recognition language (default: 'en-US')
            bucket_name: S3 bucket name for temporary audio storage (required)
        """
        self.region = region
        self.language = language
        
        # Validate bucket_name is provided
        if not bucket_name:
            raise ValueError(
                "bucket_name is required. Please provide an existing S3 bucket name "
                "or set AWS_S3_BUCKET environment variable."
            )
        
        self.bucket_name = bucket_name
        
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
        
        # Verify bucket exists and is accessible
        self._verify_bucket_access()
    
    def _verify_bucket_access(self):
        """Verify S3 bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✓ Successfully connected to S3 bucket: {self.bucket_name}")
        except Exception as e:
            error_code = e.response.get('Error', {}).get('Code', '') if hasattr(e, 'response') else ''
            
            if error_code == '404' or 'NoSuchBucket' in str(e):
                raise ValueError(
                    f"S3 bucket '{self.bucket_name}' does not exist. "
                    f"Please create the bucket first using AWS Console or CLI:\n"
                    f"  aws s3 mb s3://{self.bucket_name} --region {self.region}"
                )
            elif error_code == '403':
                raise PermissionError(
                    f"Access denied to S3 bucket '{self.bucket_name}'. "
                    f"Please check your AWS credentials have s3:GetBucketLocation permission."
                )
            else:
                raise Exception(
                    f"Failed to access S3 bucket '{self.bucket_name}': {str(e)}"
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
        # Sanitize filename for job name: replace spaces and invalid chars with underscores
        sanitized_name = filename.replace('.', '-').replace(' ', '_')
        job_name = f"transcribe-{int(time.time())}-{sanitized_name}"
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
            
            # Wait for job to complete (AWS Transcribe doesn't have built-in waiters)
            print(f"Waiting for transcription to complete: {filename}")
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            poll_interval = 5  # Poll every 5 seconds
            
            while True:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    raise TimeoutError(f"Transcription job exceeded {max_wait_time} seconds")
                
                response = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status in ['COMPLETED', 'FAILED']:
                    break
                
                time.sleep(poll_interval)
            
            # Get job status after completion
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            # Get AWS-reported timing from the job response
            job = response['TranscriptionJob']
            creation_time = job.get('CreationTime')
            completion_time = job.get('CompletionTime')
            
            aws_duration = None
            if creation_time and completion_time and status == 'COMPLETED':
                aws_duration = (completion_time - creation_time).total_seconds()
                print(f"✓ AWS transcription time: {aws_duration:.1f}s")
            
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
                    "status": "success",
                    "transcription_time": f"{aws_duration:.2f}" if aws_duration else ""
                }
            else:
                failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown')
                
                # Clean up failed job
                self.transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                
                return {
                    "filename": filename,
                    "text": "",
                    "status": f"failed: {failure_reason}",
                    "transcription_time": ""
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
                "status": f"exception: {str(e)}",
                "transcription_time": ""
            }
