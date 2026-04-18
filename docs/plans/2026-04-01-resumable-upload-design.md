# Design: Resumable Upload with Progress Tracking

## Overview

Implement resumable, chunked uploads with real-time progress bars for the `send` command. This solves:
- Large dataset uploads (>GB) failing mid-way and restarting from zero
- No visibility into upload progress
- Memory issues with large tar files

## Architecture

### Protocol Choice: **tus.io** (Recommended)

Use the **tus** protocol - an open standard for resumable HTTP uploads. Benefits:
- Industry standard (Vimeo, GitHub, Cloudflare use it)
- Simple HTTP-based protocol
- Supports parallel chunk upload
- Automatic resume on connection failure
- Existing client libraries (`tuspy`) and server middleware (`tusd`)

### Alternative: Custom Chunked Protocol

If tus is too heavy, implement lightweight custom protocol (see Appendix A).

---

## Design Components

### 1. Data Flow

```
User runs: celebi-cli send /path/to/large/dataset

1. Client creates tar.gz (streamed, not in-memory)
2. Client initiates upload session → POST /upload/create
   ← Server returns: {upload_id, chunk_size, max_chunks}
3. Client splits tar into chunks (e.g., 5MB each)
4. For each chunk:
   a. Check if already uploaded (HEAD /upload/chunk/{id}/{index})
   b. Upload with progress bar (PATCH /upload/chunk/{id}/{index})
   c. Save progress to local state file (~/.celebi/uploads/{id}.state)
5. Finalize → POST /upload/complete/{id}
6. Server verifies MD5, moves to final location
7. Clean up local state file
```

### 2. Client Implementation

#### New File: `CelebiChrono/utils/resumable_upload.py`

```python
"""Resumable upload manager with progress tracking."""
import os
import json
import hashlib
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass, asdict
import requests
from tqdm import tqdm


@dataclass
class UploadState:
    """Persistable upload state for resume capability."""
    upload_id: str
    file_path: str
    file_size: int
    file_md5: str
    chunk_size: int
    total_chunks: int
    completed_chunks: set[int]
    server_url: str
    project_uuid: str
    impression_uuid: str
    
    def to_dict(self):
        return {
            **asdict(self),
            'completed_chunks': list(self.completed_chunks)
        }
    
    @classmethod
    def from_dict(cls, data):
        data['completed_chunks'] = set(data['completed_chunks'])
        return cls(**data)


class ResumableUploader:
    """Handles chunked, resumable uploads with progress tracking."""
    
    DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
    STATE_DIR = Path.home() / ".celebi" / "uploads"
    
    def __init__(self, server_url: str, timeout: int = 30):
        self.server_url = server_url
        self.timeout = timeout
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    def upload(
        self,
        file_path: str,
        project_uuid: str,
        impression_uuid: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        resume: bool = True
    ) -> str:
        """
        Upload file with resume support and progress tracking.
        
        Args:
            file_path: Path to file to upload
            project_uuid: Project identifier
            impression_uuid: Impression identifier
            progress_callback: Optional callback(bytes_uploaded, total_bytes)
            resume: Whether to resume existing upload
            
        Returns:
            upload_id: Server-assigned upload identifier
        """
        file_size = os.path.getsize(file_path)
        file_md5 = self._calculate_md5(file_path)
        
        # Check for existing upload state
        state = None
        if resume:
            state = self._load_existing_state(file_path, file_md5)
        
        if state is None:
            # Initialize new upload
            state = self._create_upload(
                file_path, file_size, file_md5, 
                project_uuid, impression_uuid
            )
        
        # Upload chunks with progress
        self._upload_chunks(state, progress_callback)
        
        # Finalize upload
        self._finalize_upload(state)
        
        # Clean up state file
        self._remove_state_file(state.upload_id)
        
        return state.upload_id
    
    def _calculate_md5(self, file_path: str) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _load_existing_state(self, file_path: str, file_md5: str) -> Optional[UploadState]:
        """Load existing upload state if valid."""
        for state_file in self.STATE_DIR.glob("*.json"):
            try:
                with open(state_file) as f:
                    data = json.load(f)
                    state = UploadState.from_dict(data)
                    
                    # Validate state matches current file
                    if (state.file_path == file_path and 
                        state.file_md5 == file_md5 and
                        state.server_url == self.server_url):
                        
                        # Verify with server which chunks are actually uploaded
                        state.completed_chunks = self._verify_chunks_with_server(state)
                        return state
            except (json.JSONDecodeError, KeyError):
                continue
        return None
    
    def _create_upload(
        self,
        file_path: str,
        file_size: int,
        file_md5: str,
        project_uuid: str,
        impression_uuid: str
    ) -> UploadState:
        """Initialize new upload session with server."""
        response = requests.post(
            f"http://{self.server_url}/upload/create",
            json={
                "file_size": file_size,
                "file_md5": file_md5,
                "project_uuid": project_uuid,
                "impression_uuid": impression_uuid,
                "chunk_size": self.DEFAULT_CHUNK_SIZE
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        
        total_chunks = (file_size + self.DEFAULT_CHUNK_SIZE - 1) // self.DEFAULT_CHUNK_SIZE
        
        state = UploadState(
            upload_id=data["upload_id"],
            file_path=file_path,
            file_size=file_size,
            file_md5=file_md5,
            chunk_size=self.DEFAULT_CHUNK_SIZE,
            total_chunks=total_chunks,
            completed_chunks=set(),
            server_url=self.server_url,
            project_uuid=project_uuid,
            impression_uuid=impression_uuid
        )
        
        self._save_state(state)
        return state
    
    def _upload_chunks(
        self,
        state: UploadState,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """Upload chunks with progress tracking."""
        uploaded_bytes = len(state.completed_chunks) * state.chunk_size
        
        with tqdm(
            total=state.file_size,
            initial=uploaded_bytes,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            desc="Uploading"
        ) as pbar:
            
            with open(state.file_path, 'rb') as f:
                for chunk_index in range(state.total_chunks):
                    if chunk_index in state.completed_chunks:
                        continue
                    
                    # Read and upload chunk
                    f.seek(chunk_index * state.chunk_size)
                    chunk_data = f.read(state.chunk_size)
                    chunk_md5 = hashlib.md5(chunk_data).hexdigest()
                    
                    self._upload_chunk_with_retry(
                        state, chunk_index, chunk_data, chunk_md5
                    )
                    
                    state.completed_chunks.add(chunk_index)
                    self._save_state(state)
                    
                    # Update progress
                    pbar.update(len(chunk_data))
                    uploaded_bytes += len(chunk_data)
                    
                    if progress_callback:
                        progress_callback(uploaded_bytes, state.file_size)
    
    def _upload_chunk_with_retry(
        self,
        state: UploadState,
        chunk_index: int,
        chunk_data: bytes,
        chunk_md5: str,
        max_retries: int = 3
    ):
        """Upload single chunk with retry logic."""
        for attempt in range(max_retries):
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
                if attempt == max_retries - 1:
                    raise UploadError(f"Failed to upload chunk {chunk_index}: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _verify_chunks_with_server(self, state: UploadState) -> set[int]:
        """Verify with server which chunks are actually stored."""
        try:
            response = requests.get(
                f"http://{self.server_url}/upload/status/{state.upload_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return set(data.get("completed_chunks", []))
        except requests.RequestException:
            # If verification fails, assume no chunks are uploaded
            return set()
    
    def _finalize_upload(self, state: UploadState):
        """Finalize upload on server."""
        response = requests.post(
            f"http://{self.server_url}/upload/complete/{state.upload_id}",
            json={
                "project_uuid": state.project_uuid,
                "impression_uuid": state.impression_uuid
            },
            timeout=self.timeout
        )
        response.raise_for_status()
    
    def _save_state(self, state: UploadState):
        """Persist upload state to disk."""
        state_file = self.STATE_DIR / f"{state.upload_id}.json"
        with open(state_file, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)
    
    def _remove_state_file(self, upload_id: str):
        """Remove state file after successful upload."""
        state_file = self.STATE_DIR / f"{upload_id}.json"
        state_file.unlink(missing_ok=True)
    
    def list_incomplete_uploads(self) -> list[UploadState]:
        """List all incomplete uploads that can be resumed."""
        uploads = []
        for state_file in self.STATE_DIR.glob("*.json"):
            try:
                with open(state_file) as f:
                    data = json.load(f)
                    uploads.append(UploadState.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue
        return uploads
    
    def cancel_upload(self, upload_id: str):
        """Cancel and cleanup upload."""
        try:
            requests.delete(
                f"http://{self.server_url}/upload/{upload_id}",
                timeout=self.timeout
            )
        except requests.RequestException:
            pass
        self._remove_state_file(upload_id)


class UploadError(Exception):
    """Custom exception for upload failures."""
    pass
```

#### Modified: `CelebiChrono/kernel/chern_communicator.py`

```python
def deposit_with_data(self, impression, path, progress_callback=None):
    """ 
    Deposit the impression with additional data using resumable upload.
    
    Args:
        impression: Impression object
        path: Additional data path to include
        progress_callback: Optional callback(bytes_uploaded, total_bytes)
    """
    from ..utils.resumable_upload import ResumableUploader
    
    # Create temp tar file (streaming, not in-memory)
    tmpdir = "/tmp"
    tarname = f"{tmpdir}/{impression.uuid}.tar.gz"
    
    # Build tar incrementally to avoid memory issues
    self._create_tar_with_data(impression, path, tarname)
    
    # Use resumable uploader
    uploader = ResumableUploader(self.serverurl(), self.timeout)
    uploader.upload(
        file_path=tarname,
        project_uuid=self.project_uuid,
        impression_uuid=impression.uuid,
        progress_callback=progress_callback,
        resume=True
    )
    
    # Clean up temp tar
    os.unlink(tarname)
    
    # Set status to archived
    requests.get(
        f"http://{self.serverurl()}/set-job-status/{self.project_uuid}/{impression.uuid}/archived",
        timeout=self.timeout
    )

def _create_tar_with_data(self, impression, extra_path, output_path):
    """Create tar.gz with impression and extra data (streaming)."""
    import tarfile
    
    with tarfile.open(output_path, "w:gz") as tar:
        # Add impression files
        impression_tar = tarfile.open(
            self._resolve_impression_tarfile(impression), "r"
        )
        for member in impression_tar.getmembers():
            tar.addfile(member, impression_tar.extractfile(member))
        impression_tar.close()
        
        # Add extra data
        tar.add(extra_path, arcname="rawdata")
```

#### Modified: `CelebiChrono/interface/shell_modules/file_operations.py`

```python
def send(path: str) -> Message:
    """Send a path to current object with progress tracking.
    
    Supports resumable upload - if interrupted, run again to resume.
    """
    message = Message()
    
    # Show progress bar in CLI
    def progress_callback(uploaded, total):
        percent = (uploaded / total) * 100
        # tqdm handles the display, this is for additional logging if needed
    
    try:
        MANAGER.current_object().send(path, progress_callback=progress_callback)
        message.add(f"Successfully sent {path}", "success")
    except Exception as e:
        message.add(f"Upload failed: {e}", "error")
        message.add("Run 'send' again to resume upload", "info")
    
    return message
```

---

### 3. Server Implementation (Flask Example)

#### New File: Server-side upload handler

```python
"""Flask endpoints for resumable uploads."""
import os
import hashlib
import json
import uuid
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
UPLOAD_DIR = Path("/var/lib/celebi/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB


class UploadSession:
    """Server-side upload session state."""
    
    def __init__(self, upload_id, file_size, file_md5, project_uuid, impression_uuid):
        self.upload_id = upload_id
        self.file_size = file_size
        self.file_md5 = file_md5
        self.project_uuid = project_uuid
        self.impression_uuid = impression_uuid
        self.total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
        self.completed_chunks = set()
        self.session_dir = UPLOAD_DIR / upload_id
        self.session_dir.mkdir(exist_ok=True)
    
    def save(self):
        """Persist session state."""
        state_file = self.session_dir / "state.json"
        with open(state_file, 'w') as f:
            json.dump({
                'upload_id': self.upload_id,
                'file_size': self.file_size,
                'file_md5': self.file_md5,
                'project_uuid': self.project_uuid,
                'impression_uuid': self.impression_uuid,
                'total_chunks': self.total_chunks,
                'completed_chunks': list(self.completed_chunks)
            }, f)
    
    @classmethod
    def load(cls, upload_id):
        """Load existing session."""
        state_file = UPLOAD_DIR / upload_id / "state.json"
        if not state_file.exists():
            return None
        
        with open(state_file) as f:
            data = json.load(f)
        
        session = cls(
            data['upload_id'],
            data['file_size'],
            data['file_md5'],
            data['project_uuid'],
            data['impression_uuid']
        )
        session.completed_chunks = set(data['completed_chunks'])
        return session
    
    def get_chunk_path(self, chunk_index):
        return self.session_dir / f"chunk_{chunk_index}"


@app.route('/upload/create', methods=['POST'])
def create_upload():
    """Initialize new upload session."""
    data = request.json
    
    upload_id = str(uuid.uuid4())
    session = UploadSession(
        upload_id=upload_id,
        file_size=data['file_size'],
        file_md5=data['file_md5'],
        project_uuid=data['project_uuid'],
        impression_uuid=data['impression_uuid']
    )
    session.save()
    
    return jsonify({
        'upload_id': upload_id,
        'chunk_size': CHUNK_SIZE,
        'total_chunks': session.total_chunks
    })


@app.route('/upload/chunk/<upload_id>/<int:chunk_index>', methods=['PATCH'])
def upload_chunk(upload_id, chunk_index):
    """Upload a single chunk."""
    session = UploadSession.load(upload_id)
    if not session:
        return jsonify({'error': 'Upload not found'}), 404
    
    # Verify chunk MD5 if provided
    chunk_data = request.data
    expected_md5 = request.headers.get('Content-MD5')
    if expected_md5:
        actual_md5 = hashlib.md5(chunk_data).hexdigest()
        if actual_md5 != expected_md5:
            return jsonify({'error': 'Chunk MD5 mismatch'}), 400
    
    # Save chunk
    chunk_path = session.get_chunk_path(chunk_index)
    with open(chunk_path, 'wb') as f:
        f.write(chunk_data)
    
    session.completed_chunks.add(chunk_index)
    session.save()
    
    return jsonify({
        'chunk_index': chunk_index,
        'status': 'received'
    })


@app.route('/upload/status/<upload_id>', methods=['GET'])
def get_upload_status(upload_id):
    """Get upload progress."""
    session = UploadSession.load(upload_id)
    if not session:
        return jsonify({'error': 'Upload not found'}), 404
    
    return jsonify({
        'upload_id': upload_id,
        'completed_chunks': list(session.completed_chunks),
        'total_chunks': session.total_chunks,
        'progress_percent': len(session.completed_chunks) / session.total_chunks * 100
    })


@app.route('/upload/complete/<upload_id>', methods=['POST'])
def complete_upload(upload_id):
    """Finalize upload and verify."""
    session = UploadSession.load(upload_id)
    if not session:
        return jsonify({'error': 'Upload not found'}), 404
    
    # Verify all chunks received
    if len(session.completed_chunks) != session.total_chunks:
        missing = set(range(session.total_chunks)) - session.completed_chunks
        return jsonify({
            'error': 'Incomplete upload',
            'missing_chunks': list(missing)
        }), 400
    
    # Combine chunks into final file
    final_path = UPLOAD_DIR / f"{upload_id}.tar.gz"
    with open(final_path, 'wb') as outfile:
        for i in range(session.total_chunks):
            chunk_path = session.get_chunk_path(i)
            with open(chunk_path, 'rb') as infile:
                outfile.write(infile.read())
    
    # Verify final MD5
    final_md5 = calculate_file_md5(final_path)
    if final_md5 != session.file_md5:
        os.unlink(final_path)
        return jsonify({
            'error': 'Final MD5 mismatch',
            'expected': session.file_md5,
            'actual': final_md5
        }), 400
    
    # Move to final location
    project_dir = get_project_storage_path(session.project_uuid)
    dest_path = project_dir / f"{session.impression_uuid}.tar.gz"
    os.rename(final_path, dest_path)
    
    # Cleanup chunks
    import shutil
    shutil.rmtree(session.session_dir)
    
    return jsonify({
        'status': 'complete',
        'upload_id': upload_id,
        'path': str(dest_path)
    })


@app.route('/upload/<upload_id>', methods=['DELETE'])
def cancel_upload(upload_id):
    """Cancel and cleanup upload."""
    session = UploadSession.load(upload_id)
    if session:
        import shutil
        shutil.rmtree(session.session_dir, ignore_errors=True)
    
    return jsonify({'status': 'cancelled'})


def calculate_file_md5(path):
    """Calculate MD5 of a file."""
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

---

### 4. CLI Commands

Add new commands for upload management:

```bash
# Resume a specific upload
celebi-cli upload-resume <upload_id>

# List incomplete uploads
celebi-cli upload-list

# Cancel an upload
celebi-cli upload-cancel <upload_id>

# Send with explicit options
celebi-cli send /path/to/data --no-resume  # Fresh upload, ignore previous
celebi-cli send /path/to/data --chunk-size 10MB
```

---

### 5. Error Handling & Edge Cases

| Scenario | Handling |
|----------|----------|
| Network interruption | Auto-retry with exponential backoff (2^n seconds) |
| Client crash | Resume from local state file on restart |
| Server crash | Re-verify chunks with server after restart |
| MD5 mismatch | Re-upload corrupted chunk |
| Disk full | Pause upload, notify user, allow resume after cleanup |
| Duplicate upload | Detect via MD5, skip if already exists |
| Partial chunk | Overwrite partial chunk on next attempt |

---

### 6. Progress Display

```
$ celebi-cli send /path/to/dataset
Creating archive: 1.2GB... done
Initializing upload: upload_abc123
detecting existing chunks: 45/120 found (37%)

Uploading:  45%|████████████████▌                | 540M/1.2G [02:14<02:45, 4.2MB/s]
Chunk 67/120 uploaded successfully
Chunk 68/120 uploading... ▓▓▓▓▓▓▓▓░░░░░░░░ 45%

[Ctrl+C pressed - saving state]
Upload paused. Run 'celebi-cli send /path/to/dataset' to resume.
State saved: ~/.celebi/uploads/upload_abc123.json

$ celebi-cli send /path/to/dataset  # Resume
Resuming upload: upload_abc123 (45% complete)
Uploading:  78%|████████████████████████▌       | 936M/1.2G [04:12<01:20, 3.8MB/s]
...
Upload complete! ✓
```

---

## Appendix A: Alternative Lightweight Protocol

If full tus implementation is too heavy, use this minimal protocol:

```python
# Single endpoint that handles init, chunk upload, and completion
# via HTTP headers (similar to S3 multipart upload)

Headers:
- X-Upload-ID: (optional, for resume)
- X-Chunk-Index: (required for chunks)
- X-Total-Chunks: (required for first request)
- X-File-MD5: (required)
- Content-Range: bytes start-end/total

Flow:
1. POST /upload with X-Total-Chunks, X-File-MD5, no body
   → Returns X-Upload-ID
   
2. PUT /upload with X-Upload-ID, X-Chunk-Index, body=chunk
   
3. POST /upload/complete with X-Upload-ID
   → Server combines chunks
```

This requires only 2 endpoints vs 4 in the full design.

---

## Implementation Priority

1. **Week 1**: Implement client `ResumableUploader` class with local state persistence
2. **Week 2**: Add server endpoints (`/upload/create`, `/upload/chunk/*`, `/upload/complete`)
3. **Week 3**: Add progress bar (tqdm) and CLI integration
4. **Week 4**: Add resume detection, error handling, edge cases
5. **Week 5**: Testing with large files (10GB+), network interruption simulation

Total estimated effort: **3-4 weeks** for one developer.
