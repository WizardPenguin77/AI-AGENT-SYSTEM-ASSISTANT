from pathlib import Path

from system_assistant.tools.filesystem import list_directory, read_text, search_files

def test_filesystem_tools(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    assert list_directory(str(tmp_path)).ok
    assert read_text(str(tmp_path / "a.txt")).data == "hello"
    assert str(tmp_path / "a.txt") in search_files(str(tmp_path), "*.txt").data

