import os
import hashlib
import mimetypes
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("repolens.analyzer.scanner")

# Default ignore sets matching requirements
IGNORE_DIRECTORIES = {
    "node_modules", ".git", "vendor", "dist", "build", "__pycache__", 
    ".next", ".venv", "target", "coverage", ".docusaurus", ".idea", 
    ".vscode", "venv", "env"
}

IGNORE_EXTENSIONS = {
    ".exe", ".bin", ".dll", ".so", ".dylib", ".woff", ".woff2", ".ttf",
    ".eot", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip",
    ".tar", ".gz", ".rar", ".7z", ".mp3", ".mp4", ".wav", ".db", ".sqlite"
}


class CodebaseScanner:
    @staticmethod
    def calculate_sha256(filepath: str) -> str:
        """Compute SHA-256 hash of a file's content"""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except IOError as e:
            logger.error(f"IOError scanning file {filepath}: {str(e)}")
            return ""

    @staticmethod
    def get_mime_type(filepath: str) -> str:
        """Resolve content mime type from file path"""
        mime, _ = mimetypes.guess_type(filepath)
        if mime:
            return mime
            
        # Fallback text check based on extension
        _, ext = os.path.splitext(filepath)
        text_extensions = {
            ".py": "text/x-python",
            ".ts": "text/typescript",
            ".tsx": "text/typescript-react",
            ".js": "text/javascript",
            ".jsx": "text/javascript-react",
            ".go": "text/x-go",
            ".rs": "text/rust",
            ".java": Sa_type := "text/x-java-source",
            ".json": "application/json",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
            ".toml": "text/x-toml",
            ".md": "text/markdown",
            ".html": "text/html",
            ".css": "text/css",
            ".sh": "text/x-shellscript"
        }
        return text_extensions.get(ext.lower(), "application/octet-stream")

    @classmethod
    def scan(cls, root_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Recursively scan a directory.
        Returns:
            Tuple of (folders_list, files_list)
        """
        folders_list = []
        files_list = []
        
        # Absolute root resolve
        root_abs = os.path.abspath(root_path)
        
        # Keep track of directories mapped to generate parent/child references
        # Maps relative directory path to unique uuid stubs or path keys
        folder_paths = {}

        for dirpath, dirnames, filenames in os.walk(root_abs):
            # Prune directories in place to skip searching them
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRECTORIES]
            
            # Resolve relative folder path
            rel_dirpath = os.path.relpath(dirpath, root_abs)
            if rel_dirpath == ".":
                rel_dirpath = ""
                
            depth = 0 if rel_dirpath == "" else len(rel_dirpath.split(os.sep))
            name = os.path.basename(dirpath) if rel_dirpath != "" else os.path.basename(root_abs)
            
            folder_info = {
                "path": rel_dirpath,
                "name": name,
                "depth": depth,
                "size": 0  # To be accumulated
            }
            folders_list.append(folder_info)
            folder_paths[rel_dirpath] = folder_info
            
            for fname in filenames:
                _, ext = os.path.splitext(fname)
                if ext.lower() in IGNORE_EXTENSIONS:
                    continue
                    
                full_path = os.path.join(dirpath, fname)
                rel_filepath = os.path.relpath(full_path, root_abs)
                
                try:
                    if os.path.islink(full_path):
                        continue
                    size_bytes = os.path.getsize(full_path)
                    size_kb = round(size_bytes / 1024)
                    
                    # Accumulate folder sizes
                    curr_rel = rel_dirpath
                    while True:
                        if curr_rel in folder_paths:
                            folder_paths[curr_rel]["size"] += size_kb
                        if curr_rel == "":
                            break
                        curr_rel = os.path.dirname(curr_rel)

                    file_info = {
                        "path": rel_filepath,
                        "name": fname,
                        "folder_path": rel_dirpath,
                        "size": size_kb,
                        "mime_type": cls.get_mime_type(full_path),
                        "hash": cls.calculate_sha256(full_path)
                    }
                    files_list.append(file_info)
                except Exception as e:
                    logger.warning(f"Failed scanning file {full_path}: {str(e)}")

        return folders_list, files_list
