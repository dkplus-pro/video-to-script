from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from vlog_script_generator.core.config import load_config
from vlog_script_generator.core.context import RunContext
from vlog_script_generator.core.pipeline import Pipeline
from vlog_script_generator.models import ExtractedFrame, Filmstrip
from vlog_script_generator.storage.cache import write_json
from vlog_script_generator.video.filmstrip import make_filmstrips as make_filmstrips_direct

app = typer.Typer(help="中文 Vlog 素材理解与剪辑脚本生成工具")


def _context(
    input_dir: str,
    output: str = ".output",
    story: Optional[str] = None,
    config: Optional[str] = None,
    resume: bool = True,
    force: bool = False,
) -> RunContext:
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    return RunContext(
        input_dir=Path(input_dir),
        output_dir=output_dir,
        story_path=Path(story) if story else None,
        config=load_config(config),
        resume=resume,
        force=force,
    )


@app.command()
def scan(
    input: str = typer.Option(..., "--input", "-i", help="视频素材目录"),
    output: str = typer.Option(".output", "--output", "-o", help="输出目录"),
    config: Optional[str] = typer.Option(None, "--config", help="配置文件"),
) -> None:
    Pipeline(_context(input, output, config=config)).scan()


@app.command("extract-frames")
def extract_frames(
    input: str = typer.Option(..., "--input", "-i", help="视频素材目录"),
    output: str = typer.Option(".output", "--output", "-o", help="输出目录"),
    config: Optional[str] = typer.Option(None, "--config", help="配置文件"),
    force: bool = typer.Option(False, "--force", help="强制重跑"),
) -> None:
    ctx = _context(input, output, config=config, force=force)
    pipeline = Pipeline(ctx)
    metadata = pipeline.scan()
    pipeline.extract_frames(metadata)


@app.command("make-filmstrip")
def make_filmstrip(
    input: str = typer.Option(..., "--input", "-i", help="帧目录或视频目录；当前会优先读取 output/cache/frames.json"),
    output: str = typer.Option(".output", "--output", "-o", help="输出目录"),
    config: Optional[str] = typer.Option(None, "--config", help="配置文件"),
    force: bool = typer.Option(False, "--force", help="强制重跑"),
) -> None:
    ctx = _context(input, output, config=config, force=force)
    pipeline = Pipeline(ctx)
    frames_json = ctx.cache_dir / "frames.json"
    if frames_json.exists():
        pipeline.make_filmstrips()
        return
    frames = _frames_from_directory(Path(input))
    strips = make_filmstrips_direct(frames, Path(output), int(ctx.config.get("frames", {}).get("framesPerFilmstrip", 9)), force)
    write_json(Path(output) / "filmstrips.json", [item.to_dict() for item in strips])


@app.command()
def asr(
    input: str = typer.Option(..., "--input", "-i", help="视频素材目录"),
    output: str = typer.Option(".output", "--output", "-o", help="输出目录"),
    config: Optional[str] = typer.Option(None, "--config", help="配置文件"),
    force: bool = typer.Option(False, "--force", help="强制重跑"),
) -> None:
    ctx = _context(input, output, config=config, force=force)
    pipeline = Pipeline(ctx)
    metadata = pipeline.scan()
    pipeline.asr(metadata)


@app.command()
def analyze(
    input: str = typer.Option(..., "--input", "-i", help="filmstrip 目录；当前会优先读取 output/cache/filmstrips.json"),
    output: str = typer.Option(".output", "--output", "-o", help="输出目录"),
    config: Optional[str] = typer.Option(None, "--config", help="配置文件"),
    force: bool = typer.Option(False, "--force", help="强制重跑"),
) -> None:
    ctx = _context(input, output, config=config, force=force)
    pipeline = Pipeline(ctx)
    filmstrips_json = ctx.cache_dir / "filmstrips.json"
    if filmstrips_json.exists():
        pipeline.analyze()
        return
    strips = _filmstrips_from_directory(Path(input))
    analyses = [pipeline.analyze([strip])[0] for strip in strips] if strips else []
    write_json(Path(output) / "vision_analysis.json", [item.to_dict() for item in analyses])


@app.command("generate-script")
def generate_script_cmd(
    story: str = typer.Option(..., "--story", "-s", help="故事小结 Markdown"),
    materials: str = typer.Option(".output", "--materials", help="素材分析输出目录"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出目录；默认写回 materials 目录"),
    config: Optional[str] = typer.Option(None, "--config", help="配置文件"),
) -> None:
    ctx = _context(materials, output or materials, story=story, config=config)
    Pipeline(ctx).generate_script()


@app.command()
def run(
    input: str = typer.Option(..., "--input", "-i", help="视频素材目录"),
    story: str = typer.Option(..., "--story", "-s", help="故事小结 Markdown"),
    output: str = typer.Option(".output", "--output", "-o", help="输出目录"),
    config: Optional[str] = typer.Option(None, "--config", help="配置文件"),
    resume: bool = typer.Option(True, "--resume/--no-resume", help="继续已有任务"),
    force: bool = typer.Option(False, "--force", help="强制重跑"),
) -> None:
    Pipeline(_context(input, output, story, config, resume, force)).run()


def main() -> None:
    app()


def _frames_from_directory(path: Path) -> list[ExtractedFrame]:
    frames: list[ExtractedFrame] = []
    for image in sorted(path.rglob("*.jpg")):
        video_file = f"{image.parent.name}.mp4"
        ts = 0.0
        try:
            marker = image.stem.split("_")[-1].replace("ms", "")
            ts = int(marker) / 1000
        except Exception:
            pass
        frames.append(ExtractedFrame(video_file=video_file, time_seconds=ts, path=str(image)))
    return frames


def _filmstrips_from_directory(path: Path) -> list[Filmstrip]:
    strips: list[Filmstrip] = []
    for image in sorted(path.rglob("*.jpg")):
        video_file = f"{image.parent.name}.mp4"
        strips.append(Filmstrip(video_file=video_file, path=str(image), frame_paths=[], start_time=0.0, end_time=0.0))
    return strips
