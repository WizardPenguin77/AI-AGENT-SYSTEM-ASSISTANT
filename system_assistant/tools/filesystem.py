from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from system_assistant.config import MAX_FILE_BYTES
from system_assistant.models import Permission, ToolResult
from system_assistant.execution.permissions import protected_path
from system_assistant.tools.registry import RegisteredTool, ToolRegistry


class PathArgs(BaseModel): path: str
class ReadArgs(BaseModel): path: str; max_bytes: int = Field(default=MAX_FILE_BYTES, ge=1, le=MAX_FILE_BYTES)
class SearchArgs(BaseModel): root: str; pattern: str; max_results: int = Field(default=100, ge=1, le=1000)
class HashArgs(BaseModel): path: str
class WriteArgs(BaseModel): path: str; content: str = Field(max_length=1_000_000)
class DeleteArgs(BaseModel): path: str


def _path(path: str) -> Path: return Path(path).expanduser().resolve(strict=False)

def list_directory(path: str) -> ToolResult:
    target = _path(path)
    entries = [{"name": p.name, "type": "directory" if p.is_dir() else "file", "size": p.stat().st_size if p.is_file() else None} for p in target.iterdir()]
    return ToolResult(ok=True, summary=f"Listed {len(entries)} entries", data=entries)

def read_text(path: str, max_bytes: int = MAX_FILE_BYTES) -> ToolResult:
    target = _path(path)
    if target.name.lower() in {".env", ".git-credentials", "id_rsa", "id_ed25519"} or any(part.lower() in {".ssh", ".aws"} for part in target.parts):
        return ToolResult(ok=False, summary="Sensitive file not read", error="Use the separately approval-gated sensitive-file tool if access is necessary")
    return _read_text(target, max_bytes)

def _read_text(target: Path, max_bytes: int) -> ToolResult:
    if target.is_symlink() or target.stat().st_size > max_bytes: return ToolResult(ok=False, summary="File is too large or a symbolic link", error="Read safeguard triggered")
    data = target.read_bytes()
    if b"\x00" in data: return ToolResult(ok=False, summary="Binary file not read", error="Binary content")
    return ToolResult(ok=True, summary=f"Read {len(data)} bytes from {target}", data=data.decode("utf-8", errors="replace"))

def read_sensitive_text(path: str, max_bytes: int = MAX_FILE_BYTES) -> ToolResult:
    return _read_text(_path(path), max_bytes)

def search_files(root: str, pattern: str, max_results: int = 100) -> ToolResult:
    found = []
    for item in _path(root).rglob(pattern):
        if len(found) >= max_results: break
        found.append(str(item))
    return ToolResult(ok=True, summary=f"Found {len(found)} matches", data=found)

def file_hash(path: str) -> ToolResult:
    digest = hashlib.sha256()
    with _path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return ToolResult(ok=True, summary="SHA-256 calculated", data=digest.hexdigest())

def create_directory(path: str) -> ToolResult:
    target = _path(path)
    if protected_path(target): return ToolResult(ok=False, summary="Protected path denied", error="Safety policy")
    target.mkdir(parents=False, exist_ok=False)
    return ToolResult(ok=True, summary=f"Created directory {target}", changed_system=True)

def write_text_file(path: str, content: str) -> ToolResult:
    target = _path(path)
    if protected_path(target) or target.exists(): return ToolResult(ok=False, summary="Protected or existing path denied", error="No overwrite; protected paths are denied")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="")
    return ToolResult(ok=True, summary=f"Created file {target}", changed_system=True)

def delete_path(path: str) -> ToolResult:
    target = _path(path)
    if protected_path(target) or target == Path(target.anchor): return ToolResult(ok=False, summary="Destructive target denied", error="Safety policy")
    if target.is_dir(): target.rmdir()
    else: target.unlink()
    return ToolResult(ok=True, summary=f"Deleted {target}", changed_system=True)

def register(registry: ToolRegistry) -> None:
    registry.register(RegisteredTool("list_directory", "List a directory without changing it.", PathArgs, Permission.READ, list_directory))
    registry.register(RegisteredTool("read_text_file", "Read a small, non-binary text file. Never use for secrets.", ReadArgs, Permission.READ, read_text))
    registry.register(RegisteredTool("read_sensitive_text_file", "Read one sensitive text file only after explicit approval; use only when essential.", ReadArgs, Permission.WRITE, read_sensitive_text))
    registry.register(RegisteredTool("search_files", "Find paths matching a glob below a directory.", SearchArgs, Permission.READ, search_files))
    registry.register(RegisteredTool("hash_file", "Calculate a SHA-256 file hash.", HashArgs, Permission.READ, file_hash))
    registry.register(RegisteredTool("create_directory", "Create exactly one new directory; never overwrite.", PathArgs, Permission.WRITE, create_directory))
    registry.register(RegisteredTool("create_text_file", "Create a new UTF-8 text file without overwriting an existing file.", WriteArgs, Permission.WRITE, write_text_file))
    registry.register(RegisteredTool("delete_path", "Delete one empty directory or one file. This is destructive and requires approval.", DeleteArgs, Permission.DESTRUCTIVE, delete_path))

