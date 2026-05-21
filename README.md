# Vlog Script Generator

本项目是一个本地可运行的中文 Vlog 素材理解与剪辑脚本生成工具。

它不会直接剪视频，而是扫描素材、抽取关键帧、生成 filmstrip 胶片流、可选调用 ASR 和大模型分析素材，最后输出一个包含脚本、素材来源、时间范围、音效、BGM、花字和旁白建议的 Markdown 表格。

## 安装

```bash
python -m pip install -e .
```

建议本机安装 `ffmpeg` 和 `ffprobe`，用于更稳地读取视频元信息、抽音频和降级抽帧。

## 快速运行

```bash
python -m vlog_script_generator run --input ./samples/videos --story ./samples/story.md --output ./samples/output
```

## 分阶段命令

```bash
python -m vlog_script_generator scan --input ./samples/videos --output ./samples/output
python -m vlog_script_generator extract-frames --input ./samples/videos --output ./samples/output
python -m vlog_script_generator make-filmstrip --input ./samples/output/cache/frames --output ./samples/output/cache/filmstrips
python -m vlog_script_generator asr --input ./samples/videos --output ./samples/output
python -m vlog_script_generator analyze --input ./samples/output/cache/filmstrips --output ./samples/output
python -m vlog_script_generator generate-script --story ./samples/story.md --materials ./samples/output --output ./samples/output
```

## 配置

默认配置在 `config/default.yaml`，提示词在 `config/prompts.yaml`。

大模型配置支持 OpenAI Compatible API：

```yaml
llm:
  provider: openai-compatible
  baseURL: "https://api.example.com/v1"
  apiKey: "${API_KEY}"
  textModel: "deepseek-chat"
  visionModel: "qwen-vl-plus"
```

没有配置 API Key 时，工具会使用本地启发式分析和模板生成，保证流程可验证。

