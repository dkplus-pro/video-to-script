from __future__ import annotations

try:
    from rich.console import Console
except ImportError:  # pragma: no cover
    Console = None


class ProgressReporter:
    def __init__(self) -> None:
        self.console = Console() if Console else None

    def stage(self, index: int, total: int, message: str) -> None:
        text = f"[{index}/{total}] {message}"
        if self.console:
            self.console.print(f"[bold cyan]{text}[/bold cyan]")
        else:
            print(text)

    def info(self, message: str) -> None:
        if self.console:
            self.console.print(message)
        else:
            print(message)

    def warn(self, message: str) -> None:
        if self.console:
            self.console.print(f"[yellow]{message}[/yellow]")
        else:
            print(f"WARNING: {message}")

