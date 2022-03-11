import os

from rich.console import Console, RenderableType


def render_as_string(renderable: RenderableType) -> str:
    """Render any `rich` object in a fake console and
    return a *style-less* version of it as a string."""

    with open(os.devnull, "w") as null_stream:
        fake_console = Console(
            file=null_stream,
            stderr=null_stream,
            record=True
        )
        fake_console.print(renderable)
        return fake_console.export_text()
