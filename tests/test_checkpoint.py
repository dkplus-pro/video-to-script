from pathlib import Path

from vlog_script_generator.storage.checkpoint import Checkpoint


def test_checkpoint_marks_step(tmp_path: Path):
    path = tmp_path / "task_state.json"
    checkpoint = Checkpoint(path, tmp_path)
    checkpoint.mark_step("scan", "done")
    assert checkpoint.is_step_done("scan")
    assert path.exists()

