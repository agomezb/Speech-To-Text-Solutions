"""
Amazon Transcribe Speech-to-Text Service
Handles speech-to-text transcription using AWS Transcribe.
"""

import os
import time
import boto3
from typing import Dict, List
from pathlib import Path
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
        super().__init__()
        self.provider_name = "amazon"
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
    
    def transcribe_directory(
        self,
        audio_dir: str,
        output_csv: str,
        supported_extensions: tuple = ('.wav', '.mp3', '.ogg', '.flac')
    ) -> None:
        """
        Transcribe all audio files in a directory using batch processing.
        Overrides base class to use parallel processing for better performance.
        
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
        
        # Use batch processing
        results = self._batch_transcribe(audio_files)
        
        # Save to CSV
        self._save_to_csv(results, output_csv)
        print(f"\nResults saved to: {output_csv}")
    
    def _batch_transcribe(self, audio_files: List[str]) -> List[Dict[str, str]]:
        """
        Transcribe multiple audio files in batch using parallel job submission.
        
        Args:
            audio_files: List of audio file paths
            
        Returns:
            List of transcription results
        """
        # Step 1: Upload all files to S3
        jobs = self._upload_files_to_s3(audio_files)
        
        # Step 2: Start all transcription jobs
        self._start_transcription_jobs(jobs)
        
        # Step 3: Wait for all jobs to complete
        self._wait_for_jobs_completion(jobs)
        
        # Step 4: Process results and cleanup
        results = self._process_results_and_cleanup(jobs)
        
        return results
    
    def _upload_files_to_s3(self, audio_files: List[str]) -> Dict:
        """
        Upload audio files to S3 bucket.
        
        Args:
            audio_files: List of audio file paths
            
        Returns:
            Dictionary mapping job names to file info
        """
        print("\n📤 Uploading files to S3...")
        jobs = {}
        
        for audio_file_path in sorted(audio_files, key=self._natural_sort_key):
            filename = os.path.basename(audio_file_path)
            sanitized_name = filename.replace('.', '-').replace(' ', '_')
            job_name = f"transcribe-{int(time.time() * 1000)}-{sanitized_name}"
            s3_key = f"audio/{filename}"
            
            try:
                print(f"  Uploading: {filename}")
                self.s3_client.upload_file(audio_file_path, self.bucket_name, s3_key)
                
                jobs[job_name] = {
                    'filename': filename,
                    's3_key': s3_key,
                    'audio_file_path': audio_file_path,
                    'status': 'uploaded'
                }
                
                time.sleep(0.01)  # Ensure unique timestamps
                
            except Exception as e:
                jobs[job_name] = {
                    'filename': filename,
                    's3_key': s3_key,
                    'audio_file_path': audio_file_path,
                    'status': 'upload_failed',
                    'error': str(e)
                }
        
        return jobs
    
    def _start_transcription_jobs(self, jobs: Dict) -> None:
        """
        Start AWS Transcribe jobs for all uploaded files.
        
        Args:
            jobs: Dictionary mapping job names to file info (modified in place)
        """
        print("\n🚀 Starting transcription jobs...")
        
        for job_name, job_info in jobs.items():
            if job_info['status'] != 'uploaded':
                continue
            
            try:
                filename = job_info['filename']
                s3_key = job_info['s3_key']
                media_uri = f"s3://{self.bucket_name}/{s3_key}"
                
                self.transcribe_client.start_transcription_job(
                    TranscriptionJobName=job_name,
                    Media={'MediaFileUri': media_uri},
                    MediaFormat=filename.split('.')[-1],
                    LanguageCode=self.language
                )
                
                jobs[job_name]['status'] = 'submitted'
                print(f"  Started: {filename}")
                
            except Exception as e:
                jobs[job_name]['status'] = 'submit_failed'
                jobs[job_name]['error'] = str(e)
                print(f"  Failed to start: {filename} - {e}")
    
    def _wait_for_jobs_completion(self, jobs: Dict) -> None:
        """
        Poll AWS Transcribe jobs until all are completed or failed.
        
        Args:
            jobs: Dictionary mapping job names to file info (modified in place)
        """
        print("\n⏳ Waiting for all transcriptions to complete...")
        
        submitted_jobs = {k: v for k, v in jobs.items() if v['status'] == 'submitted'}
        max_wait_time = 600  # 10 minutes
        start_time = time.time()
        poll_interval = 5
        completed_count = 0
        total_jobs = len(submitted_jobs)
        
        while submitted_jobs:
            if time.time() - start_time > max_wait_time:
                print(f"  ⚠️  Timeout reached, {len(submitted_jobs)} jobs still pending")
                break
            
            jobs_to_remove = []
            
            for job_name, job_info in submitted_jobs.items():
                try:
                    response = self.transcribe_client.get_transcription_job(
                        TranscriptionJobName=job_name
                    )
                    
                    # Verify response matches requested job
                    response_job_name = response['TranscriptionJob']['TranscriptionJobName']
                    if response_job_name != job_name:
                        raise ValueError(
                            f"Job name mismatch: requested '{job_name}', got '{response_job_name}'"
                        )
                    
                    status = response['TranscriptionJob']['TranscriptionJobStatus']
                    
                    if status in ['COMPLETED', 'FAILED']:
                        jobs[job_name]['response'] = response
                        jobs[job_name]['status'] = status.lower()
                        jobs_to_remove.append(job_name)
                        
                        completed_count += 1
                        print(f"  ✓ Completed {completed_count}/{total_jobs}: {job_info['filename']}")
                        
                except Exception as e:
                    jobs[job_name]['status'] = 'check_failed'
                    jobs[job_name]['error'] = str(e)
                    jobs_to_remove.append(job_name)
            
            for job_name in jobs_to_remove:
                del submitted_jobs[job_name]
            
            if submitted_jobs:
                time.sleep(poll_interval)
    
    def _process_results_and_cleanup(self, jobs: Dict) -> List[Dict[str, str]]:
        """
        Process transcription results and cleanup S3 files.
        
        Args:
            jobs: Dictionary mapping job names to file info
            
        Returns:
            List of transcription results
        """
        import json
        import urllib.request
        import ssl
        
        print("\n📥 Processing results...")
        results = []
        s3_keys_to_delete = []
        
        # Create SSL context for downloading transcripts
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        for job_name, job_info in jobs.items():
            filename = job_info['filename']
            s3_key = job_info['s3_key']
            s3_keys_to_delete.append({'Key': s3_key})
            
            result = self._process_single_job_result(job_info, job_name, ssl_context)
            
            # Add provider name and metadata
            result['provider'] = self.provider_name
            self._add_filename_metadata(result, filename)
            
            results.append(result)
        
        # Batch delete all S3 files
        self._cleanup_s3_files(s3_keys_to_delete)
        
        return results
    
    def _process_single_job_result(self, job_info: Dict, job_name: str, ssl_context) -> Dict[str, str]:
        """
        Process result for a single transcription job.
        
        Args:
            job_info: Job information dictionary
            job_name: AWS Transcribe job name
            ssl_context: SSL context for downloading transcripts
            
        Returns:
            Result dictionary with filename, text, status, and transcription_time
        """
        import json
        import urllib.request
        
        filename = job_info['filename']
        
        try:
            if job_info['status'] == 'completed':
                response = job_info['response']
                job_data = response['TranscriptionJob']
                
                # Get timing information
                creation_time = job_data.get('CreationTime')
                completion_time = job_data.get('CompletionTime')
                aws_duration = None
                
                if creation_time and completion_time:
                    aws_duration = (completion_time - creation_time).total_seconds()
                
                # Download and parse transcript
                transcript_uri = job_data['Transcript']['TranscriptFileUri']
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
                
            elif job_info['status'] == 'failed':
                response = job_info['response']
                failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown')
                
                # Clean up failed job
                self.transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                
                return {
                    "filename": filename,
                    "text": "",
                    "status": f"failed: {failure_reason}",
                    "transcription_time": ""
                }
            else:
                # Upload failed, submit failed, or other error
                error_msg = job_info.get('error', job_info['status'])
                return {
                    "filename": filename,
                    "text": "",
                    "status": f"error: {error_msg}",
                    "transcription_time": ""
                }
                
        except Exception as e:
            return {
                "filename": filename,
                "text": "",
                "status": f"exception: {str(e)}",
                "transcription_time": ""
            }
    
    def _add_filename_metadata(self, result: Dict, filename: str) -> None:
        """
        Extract and add metadata from filename to result dictionary.
        Expected format: {person}_{audio}_{noise}_{snr}.ext
        
        Args:
            result: Result dictionary (modified in place)
            filename: Audio filename
        """
        filename_stem = Path(filename).stem
        parts = filename_stem.split('_')
        
        if len(parts) > 0: result['person'] = parts[0]
        if len(parts) > 1: result['audio'] = parts[1]
        if len(parts) > 2: result['noise'] = parts[2]
        if len(parts) > 3: result['snr'] = parts[3]
    
    def _cleanup_s3_files(self, s3_keys_to_delete: List[Dict]) -> None:
        """
        Delete files from S3 bucket in batch.
        
        Args:
            s3_keys_to_delete: List of S3 keys to delete
        """
        if not s3_keys_to_delete:
            return
        
        print(f"\n🗑️  Deleting {len(s3_keys_to_delete)} files from S3...")
        
        try:
            # S3 delete_objects can handle up to 1000 objects per call
            for i in range(0, len(s3_keys_to_delete), 1000):
                batch = s3_keys_to_delete[i:i+1000]
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': batch}
                )
            print(f"✓ Cleanup complete")
        except Exception as e:
            print(f"⚠️  Warning: S3 cleanup failed: {e}")
