from __future__ import annotations

from rich.color import Color
from rich.console import Group, RenderableType
from rich.style import Style
from rich.text import Text

STYLE_PROPERTY_NAME = Style(color=Color.from_rgb(199, 125, 187))
STYLE_KEYWORDS = Style(color=Color.from_rgb(207, 142, 109))
STYLE_NUMBER = Style(color=Color.from_rgb(42, 172, 184))
STYLE_STRING = Style(color=Color.from_rgb(106, 171, 115))
STYLE_FUNCTION = Style(color=Color.from_rgb(136, 136, 198))

class Inline:
    def __init__(self, *renderables: RenderableType) -> None:
        self.renderables: list[RenderableType] = []
        for renderable in renderables:
            match renderable:
                case str() as text:
                    self.renderables.append(Text(text, end=""))
                case Text() as text:
                    text = text.copy()
                    text.end = ""
                    self.renderables.append(text)
                case _:
                    self.renderables.append(renderable)
    def __rich__(self) -> Group:
        return Group(*self.renderables)
