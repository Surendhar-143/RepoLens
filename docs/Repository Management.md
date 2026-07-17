# Repository Management Manual

RepoLens manages codebase caching and cloning pipelines asynchronously to handle massive, complex software repositories safely.

## Importing Methods
1. **GitHub Clone Repository**: Pasting a clone URL initiates a GitPython fetch cloning the project to `/workspace_cache/<repo-uuid>`.
2. **ZIP Archive Uploads**: Drag-and-dropping local repositories as ZIP uploads extracts contents to cache.

### Security Mitigations
* **Zip Slip Vulnerability Check**: The worker validates all compressed path headers during zip extractions, matching against targets to prevent arbitrary file writes:
  ```python
  target_file = os.path.abspath(os.path.join(local_path, member.filename))
  if not target_file.startswith(os.path.abspath(local_path)):
      raise Exception("Path traversal attempt detected.")
  ```
* **Limits**: Uploaded folder zips must not exceed 50MB.

---

## Workspace Storage and Deletions
* Cloned code files reside locally in `/workspace_cache` named by repository UUIDs.
* **Deletion**: Clicking delete soft-deletes database profiles (sets `is_deleted=True`) and dispatches background worker tasks to safely purge all disk cache folders.
