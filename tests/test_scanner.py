from pathlib import Path

from vlog_script_generator.video.scanner import scan_video_files


def test_scan_video_files(tmp_path: Path):
    (tmp_path / "a.mp4").write_text("", encoding="utf-8")
    (tmp_path / "b.txt").write_text("", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.MOV").write_text("", encoding="utf-8")
    found = scan_video_files(tmp_path)
    assert [p.name for p in found] == ["a.mp4", "c.MOV"]

