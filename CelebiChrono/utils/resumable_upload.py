"""Resumable upload manager with progress tracking for Celebi.

This module provides chunked, resumable file uploads with real-time progress
tracking. It handles network interruptions, allows resume from previous state,
and provides memory-efficient streaming for large files.

Example:
    uploader = ResumableUploader("localhost:5000")
    upload_id = uploader.upload(
        file_path="/path/to/large/file.tar.gz",
        project_uuid="proj-123",
        impression_uuid="imp-456",
        progress_callback=lambda uploaded, total: print(f"{uploaded}/{total}")
    )
"""
import os
import json
import hashlib
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Callable, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


@dataclass
class UploadState:
    """Persistable upload state for resume capability.

    Attributes:
        upload_id: Server-assigned upload identifier
        file_path: Local path to the file being uploaded
        file_size: Total size of the file in bytes
        file_md5: MD5 hash of the entire file
        chunk_size: Size of each chunk in bytes
        total_chunks: Total number of chunks
        completed_chunks: Set of chunk indices already uploaded
        server_url: Base URL of the upload server
        project_uuid: Project identifier
        impression_uuid: Impression identifier
    """
    upload_id: str
    file_path: str
    file_size: int
    file_md5: str
    chunk_size: int
    total_chunks: int
    completed_chunks: Set[int]
    server_url: str
    project_uuid: str
    impression_uuid: str

    def to_dict(self) -> dict:
        """Convert state to dictionary for JSON serialization."""
        return {
            **asdict(self),
            'completed_chunks': list(self.completed_chunks)
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UploadState':
        """Create UploadState from dictionary."""
        data['completed_chunks'] = set(data['completed_chunks'])
        return cls(**data)


class UploadError(Exception):
    """Exception raised for upload-related errors."""
    pass


class ResumableUploader:
    """Handles chunked, resumable uploads with progress tracking.

    This class manages the upload of large files by splitting them into chunks,
    tracking progress, and allowing resume from interruptions. Upload state is
    persisted to disk to enable recovery from client crashes.

    Attributes:
        DEFAULT_CHUNK_SIZE: Default size of upload chunks (5MB)
        STATE_DIR: Directory for persisting upload state files
        MAX_RETRIES: Maximum retry attempts per chunk
        RETRY_BACKOFF_BASE: Base for exponential backoff calculation
    """

    DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
    STATE_DIR = Path.home() / ".celebi" / "uploads"
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2

    def __init__(self, server_url: str, timeout: int = 30):
        """Initialize the uploader.

        Args:
            server_url: Base URL of the upload server (e.g., "localhost:5000")
            timeout: Default timeout for HTTP requests in seconds
        """
        self.server_url = server_url
        self.timeout = timeout
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)

    def upload(
        self,
        file_path: str,
        project_uuid: str,
        impression_uuid: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        resume: bool = True,
        chunk_size: Optional[int] = None,
        parallel_chunks: int = 1
    ) -> str:
        """Upload a file with resume support and progress tracking.

        Args:
            file_path: Path to the file to upload
            project_uuid: Project identifier
            impression_uuid: Impression identifier
            progress_callback: Optional callback(bytes_uploaded, total_bytes)
            resume: Whether to resume existing upload if found
            chunk_size: Override default chunk size (bytes)
            parallel_chunks: Number of parallel chunk uploads (default: 1)

        Returns:
            upload_id: Server-assigned upload identifier

        Raises:
            UploadError: If upload fails after retries
            FileNotFoundError: If file_path doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        file_md5 = self._calculate_md5(file_path)
        actual_chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE

        # Check for existing upload state
        state = None
        if resume:
            state = self._load_existing_state(file_path, file_md5)

        if state is None:
            # Initialize new upload
            state = self._create_upload(
                file_path=file_path,
                file_size=file_size,
                file_md5=file_md5,
                chunk_size=actual_chunk_size,
                project_uuid=project_uuid,
                impression_uuid=impression_uuid
            )

        try:
            # Upload chunks with progress
            if parallel_chunks > 1:
                self._upload_chunks_parallel(
                    state, progress_callback, parallel_chunks
                )
            else:
                self._upload_chunks_sequential(state, progress_callback)

            # Finalize upload
            self._finalize_upload(state)

            # Clean up state file
            self._remove_state_file(state.upload_id)

            return state.upload_id

        except Exception as e:
            # Save state before re-raising to allow resume
            self._save_state(state)
            raise UploadError(f"Upload failed: {e}") from e

    def cancel_upload(self, upload_id: str) -> None:
        """Cancel an upload and clean up resources.

        Args:
            upload_id: The upload identifier to cancel
        """
        try:
            requests.delete(
                f"http://{self.server_url}/upload/{upload_id}",
                timeout=self.timeout
            )
        except requests.RequestException:
            pass  # Ignore cleanup errors
        self._remove_state_file(upload_id)

    def list_incomplete_uploads(self) -> list[UploadState]:
        """List all incomplete uploads that can be resumed.

        Returns:
            List of UploadState objects for incomplete uploads
        """
        uploads = []
        for state_file in self.STATE_DIR.glob("*.json"):
            try:
                with open(state_file, encoding='utf-8') as f:
                    data = json.load(f)
                    uploads.append(UploadState.from_dict(data))
            except (json.JSONDecodeError, KeyError, OSError):
                continue
        return uploads

    def _calculate_md5(self, file_path: str) -> str:
        """Calculate MD5 hash of a file efficiently.

        Reads the file in chunks to avoid memory issues with large files.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal MD5 hash string
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _calculate_chunk_md5(self, file_path: str, chunk_index: int,
                             chunk_size: int) -> str:
        """Calculate MD5 hash of a specific chunk.

        Args:
            file_path: Path to the file
            chunk_index: Index of the chunk
            chunk_size: Size of each chunk

        Returns:
            Hexadecimal MD5 hash of the chunk
        """
        hash_md5 = hashlib.md5()
        offset = chunk_index * chunk_size

        with open(file_path, "rb") as f:
            f.seek(offset)
            remaining = chunk_size
            while remaining > 0:
                read_size = min(8192, remaining)
                data = f.read(read_size)
                if not data:
                    break
                hash_md5.update(data)
                remaining -= len(data)

        return hash_md5.hexdigest()

    def _load_existing_state(self, file_path: str,
                             file_md5: str) -> Optional[UploadState]:
        """Load and validate existing upload state.

        Args:
            file_path: Path to check for existing uploads
            file_md5: MD5 hash of the current file

        Returns:
            UploadState if valid resume found, None otherwise
        """
        for state_file in self.STATE_DIR.glob("*.json"):
            try:
                with open(state_file, encoding='utf-8') as f:
                    data = json.load(f)
                    state = UploadState.from_dict(data)

                    # Validate state matches current file and server
                    if (state.file_path == file_path and
                        state.file_md5 == file_md5 and
                        state.server_url == self.server_url):

                        # Verify with server which chunks exist
                        state.completed_chunks = self._verify_chunks_with_server(state)
                        return state

            except (json.JSONDecodeError, KeyError, OSError):
                continue

        return None

    def _create_upload(
        self,
        file_path: str,
        file_size: int,
        file_md5: str,
        chunk_size: int,
        project_uuid: str,
        impression_uuid: str
    ) -> UploadState:
        """Initialize a new upload session with the server.

        Args:
            file_path: Local file path
            file_size: Size of the file
            file_md5: MD5 hash of the file
            chunk_size: Chunk size for upload
            project_uuid: Project identifier
            impression_uuid: Impression identifier

        Returns:
            UploadState for the new upload

        Raises:
            UploadError: If server communication fails
        """
        total_chunks = (file_size + chunk_size - 1) // chunk_size

        try:
            response = requests.post(
                f"http://{self.server_url}/upload/create",
                json={
                    "file_size": file_size,
                    "file_md5": file_md5,
                    "project_uuid": project_uuid,
                    "impression_uuid": impression_uuid,
                    "chunk_size": chunk_size,
                    "total_chunks": total_chunks
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            state = UploadState(
                upload_id=data["upload_id"],
                file_path=file_path,
                file_size=file_size,
                file_md5=file_md5,
                chunk_size=chunk_size,
                total_chunks=total_chunks,
                completed_chunks=set(),
                server_url=self.server_url,
                project_uuid=project_uuid,
                impression_uuid=impression_uuid
            )

            self._save_state(state)
            return state

        except requests.RequestException as e:
            raise UploadError(f"Failed to create upload: {e}") from e

    def _upload_chunks_sequential(
        self,
        state: UploadState,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> None:
        """Upload chunks sequentially with progress tracking.

        Args:
            state: Current upload state
            progress_callback: Optional progress callback
        """
        uploaded_bytes = len(state.completed_chunks) * state.chunk_size
        uploaded_bytes = min(uploaded_bytes, state.file_size)

        # Calculate chunks to upload
        chunks_to_upload = [
            i for i in range(state.total_chunks)
            if i not in state.completed_chunks
        ]

        with open(state.file_path, 'rb') as f:
            for chunk_index in chunks_to_upload:
                # Seek to chunk position
                f.seek(chunk_index * state.chunk_size)
                chunk_data = f.read(state.chunk_size)

                # Upload with retry
                self._upload_chunk_with_retry(state, chunk_index, chunk_data)

                # Update state
                state.completed_chunks.add(chunk_index)
                self._save_state(state)

                # Update progress
                uploaded_bytes += len(chunk_data)
                uploaded_bytes = min(uploaded_bytes, state.file_size)

                if progress_callback:
                    progress_callback(uploaded_bytes, state.file_size)

    def _upload_chunks_parallel(
        self,
        state: UploadState,
        progress_callback: Optional[Callable[[int, int], None]],
        max_workers: int
    ) -> None:
        """Upload chunks in parallel with progress tracking.

        Args:
            state: Current upload state
            progress_callback: Optional progress callback
            max_workers: Maximum number of parallel uploads
        """
        chunks_to_upload = [
            i for i in range(state.total_chunks)
            if i not in state.completed_chunks
        ]

        completed_count = len(state.completed_chunks)
        total_count = state.total_chunks

        def upload_single(chunk_index: int) -> int:
            """Upload a single chunk and return its index."""
            with open(state.file_path, 'rb') as f:
                f.seek(chunk_index * state.chunk_size)
                chunk_data = f.read(state.chunk_size)

            self._upload_chunk_with_retry(state, chunk_index, chunk_data)
            return chunk_index

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(upload_single, idx): idx
                for idx in chunks_to_upload
            }

            for future in as_completed(futures):
                chunk_index = futures[future]
                try:
                    future.result()
                    state.completed_chunks.add(chunk_index)
                    self._save_state(state)

                    completed_count += 1
                    if progress_callback:
                        progress_callback(
                            completed_count * state.chunk_size,
                            state.file_size
                        )

                except Exception as e:
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    raise UploadError(f"Failed to upload chunk {chunk_index}: {e}") from e

    def _upload_chunk_with_retry(
        self,
        state: UploadState,
        chunk_index: int,
        chunk_data: bytes
    ) -> None:
        """Upload a single chunk with exponential backoff retry.

        Args:
            state: Current upload state
            chunk_index: Index of the chunk to upload
            chunk_data: Binary data of the chunk

        Raises:
            UploadError: If all retry attempts fail
        """
        chunk_md5 = hashlib.md5(chunk_data).hexdigest()

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.patch(
                    f"http://{self.server_url}/upload/chunk/{state.upload_id}/{chunk_index}",
                    data=chunk_data,
                    headers={
                        "Content-MD5": chunk_md5,
                        "Content-Type": "application/octet-stream"
                    },
                    timeout=60  # Longer timeout for chunk upload
                )
                response.raise_for_status()
                return

            except requests.RequestException as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise UploadError(
                        f"Failed to upload chunk {chunk_index} after "
                        f"{self.MAX_RETRIES} attempts: {e}"
                    ) from e

                # Exponential backoff
                sleep_time = self.RETRY_BACKOFF_BASE ** attempt
                time.sleep(sleep_time)

    def _verify_chunks_with_server(self, state: UploadState) -> Set[int]:
        """Verify with server which chunks are actually stored.

        Args:
            state: Current upload state

        Returns:
            Set of verified chunk indices
        """
        try:
            response = requests.get(
                f"http://{self.server_url}/upload/status/{state.upload_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return set(data.get("completed_chunks", []))
        except requests.RequestException:
            # If verification fails, trust local state
            return state.completed_chunks

    def _finalize_upload(self, state: UploadState) -> None:
        """Finalize the upload on the server.

        Args:
            state: Upload state to finalize

        Raises:
            UploadError: If finalization fails
        """
        try:
            response = requests.post(
                f"http://{self.server_url}/upload/complete/{state.upload_id}",
                json={
                    "project_uuid": state.project_uuid,
                    "impression_uuid": state.impression_uuid
                },
                timeout=self.timeout
            )
            response.raise_for_status()

        except requests.RequestException as e:
            raise UploadError(f"Failed to finalize upload: {e}") from e

    def _save_state(self, state: UploadState) -> None:
        """Persist upload state to disk.

        Args:
            state: State to persist
        """
        state_file = self.STATE_DIR / f"{state.upload_id}.json"
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, indent=2)
        except OSError as e:
            # Log but don't fail - upload can continue without state persistence
            print(f"Warning: Failed to save upload state: {e}")

    def _remove_state_file(self, upload_id: str) -> None:
        """Remove the state file after successful upload.

        Args:
            upload_id: ID of the upload to clean up
        """
        state_file = self.STATE_DIR / f"{upload_id}.json"
        try:
            state_file.unlink(missing_ok=True)
        except OSError:
            pass  # Ignore cleanup errors
