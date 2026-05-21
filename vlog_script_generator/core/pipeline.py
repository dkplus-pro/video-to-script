from __future__ import annotations

from pathlib import Path

from vlog_script_generator.audio.asr import transcribe_video
from vlog_script_generator.core.context import RunContext
from vlog_script_generator.core.progress import ProgressReporter
from vlog_script_generator.llm.prompts import load_prompts
from vlog_script_generator.llm.vision_analyzer import analyze_filmstrip
from vlog_script_generator.models import AsrSegment, ExtractedFrame, Filmstrip, MaterialAnalysis, VideoMetadata, ensure_dir
from vlog_script_generator.output.markdown_writer import write_markdown
from vlog_script_generator.storage.cache import read_json, write_json
from vlog_script_generator.storage.checkpoint import Checkpoint
from vlog_script_generator.story.script_writer import generate_script
from vlog_script_generator.video.filmstrip import make_filmstrips
from vlog_script_generator.video.frame_extractor import extract_frames_for_video
from vlog_script_generator.video.metadata import read_metadata
from vlog_script_generator.video.scanner import scan_video_files


class Pipeline:
    def __init__(self, context: RunContext) -> None:
        self.context = context
        self.progress = ProgressReporter()
        self.checkpoint = Checkpoint(context.checkpoints_dir / "task_state.json", context.input_dir)
        self.prompts = load_prompts()

    def scan(self) -> list[VideoMetadata]:
        self.progress.stage(1, 6, "扫描素材并读取元信息...")
        files = scan_video_files(self.context.input_dir, self.context.config.get("video", {}).get("extensions"))
        metadata = [read_metadata(path) for path in files]
        out_path = self.context.output_dir / "material_index.json"
        write_json(out_path, [item.to_dict() for item in metadata])
        self.checkpoint.mark_step("scan", "done", str(out_path))
        self.progress.info(f"已生成素材清单：{out_path}")
        return metadata

    def extract_frames(self, metadata: list[VideoMetadata] | None = None) -> list[ExtractedFrame]:
        self.progress.stage(2, 6, "智能抽帧并过滤黑屏/模糊帧...")
        metadata = metadata or self._load_metadata()
        frame_root = ensure_dir(self.context.cache_dir / "frames")
        frames: list[ExtractedFrame] = []
        for meta in metadata:
            if not meta.readable:
                continue
            frames.extend(extract_frames_for_video(meta.path, meta, frame_root, self.context.config, self.context.force))
            self.checkpoint.mark_video(meta.file_name, "frames", "done")
        out_path = self.context.cache_dir / "frames.json"
        write_json(out_path, [item.to_dict() for item in frames])
        self.checkpoint.mark_step("extract_frames", "done", str(out_path))
        return frames

    def make_filmstrips(self, frames: list[ExtractedFrame] | None = None) -> list[Filmstrip]:
        self.progress.stage(3, 6, "生成 filmstrip 胶片流...")
        frames = frames or self._load_frames()
        frames_per = int(self.context.config.get("frames", {}).get("framesPerFilmstrip", 9))
        strips = make_filmstrips(frames, self.context.cache_dir / "filmstrips", frames_per, self.context.force)
        out_path = self.context.cache_dir / "filmstrips.json"
        write_json(out_path, [item.to_dict() for item in strips])
        self.checkpoint.mark_step("make_filmstrip", "done", str(out_path))
        return strips

    def asr(self, metadata: list[VideoMetadata] | None = None) -> dict[str, list[AsrSegment]]:
        self.progress.stage(4, 6, "提取音频并生成 ASR 字幕...")
        metadata = metadata or self._load_metadata()
        out_root = ensure_dir(self.context.cache_dir / "asr")
        result: dict[str, list[AsrSegment]] = {}
        for meta in metadata:
            if not meta.readable:
                continue
            segments = transcribe_video(meta.path, out_root, self.context.config, self.context.force)
            result[meta.file_name] = segments
            self.checkpoint.mark_video(meta.file_name, "asr", "done")
        self.checkpoint.mark_step("asr", "done", str(out_root))
        return result

    def analyze(self, strips: list[Filmstrip] | None = None) -> list[MaterialAnalysis]:
        self.progress.stage(5, 6, "分析胶片流素材...")
        strips = strips or self._load_filmstrips()
        analyses = [
            analyze_filmstrip(strip, self.context.cache_dir / "vision_analysis", self.context.config, self.prompts, self.context.force)
            for strip in strips
        ]
        out_path = self.context.cache_dir / "vision_analysis.json"
        write_json(out_path, [item.to_dict() for item in analyses])
        self.checkpoint.mark_step("analyze", "done", str(out_path))
        return analyses

    def generate_script(self, metadata: list[VideoMetadata] | None = None, analyses: list[MaterialAnalysis] | None = None, asr: dict[str, list[AsrSegment]] | None = None) -> Path:
        self.progress.stage(6, 6, "生成 Markdown 视频脚本...")
        if not self.context.story_path:
            raise ValueError("generate-script/run requires --story")
        metadata = metadata or self._load_metadata()
        analyses = analyses or self._load_analyses()
        asr = asr or self._load_asr()
        content = generate_script(self.context.story_path, metadata, analyses, asr, self.context.config, self.prompts)
        out_path = write_markdown(self.context.final_dir / "video_script.md", content)
        self.checkpoint.mark_step("generate_script", "done", str(out_path))
        self.progress.info(f"脚本已输出：{out_path}")
        return out_path

    def run(self) -> Path:
        metadata = self.scan()
        frames = self.extract_frames(metadata)
        strips = self.make_filmstrips(frames)
        asr = self.asr(metadata)
        analyses = self.analyze(strips)
        return self.generate_script(metadata, analyses, asr)

    def _load_metadata(self) -> list[VideoMetadata]:
        data = read_json(self.context.output_dir / "material_index.json", []) or []
        return [VideoMetadata(**item) for item in data]

    def _load_frames(self) -> list[ExtractedFrame]:
        data = read_json(self.context.cache_dir / "frames.json", []) or []
        return [ExtractedFrame(**item) for item in data]

    def _load_filmstrips(self) -> list[Filmstrip]:
        data = read_json(self.context.cache_dir / "filmstrips.json", []) or []
        return [Filmstrip(**item) for item in data]

    def _load_analyses(self) -> list[MaterialAnalysis]:
        data = read_json(self.context.cache_dir / "vision_analysis.json", []) or []
        return [MaterialAnalysis(**item) for item in data]

    def _load_asr(self) -> dict[str, list[AsrSegment]]:
        result: dict[str, list[AsrSegment]] = {}
        for path in (self.context.cache_dir / "asr").glob("*/asr.json"):
            data = read_json(path, {}) or {}
            result[data.get("video", path.parent.name)] = [AsrSegment(**item) for item in data.get("segments", [])]
        return result

