from collections import ChainMap
from typing import TYPE_CHECKING, Any, Optional, List
from enum import Enum, auto
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from rich.theme import Theme

from httpie.output.ui.palette.pie import (
    PIE_STYLE_TO_SHADE,
    PieStyle,
    PieColor,
    get_color,
)  # noqa


class RichTheme(Enum):
    """Represents the color theme to use within rich."""
    PIE = auto()
    ANSI = auto()

    @classmethod
    def from_style_name(cls, style_name: str) -> 'RichTheme':
        try:
            PieStyle(style_name)
        except ValueError:
            return RichTheme.ANSI
        else:
            return RichTheme.PIE


class RichColor(Enum):
    """Generic colors that are safe to use everywhere within rich."""

    # <https://rich.readthedocs.io/en/stable/appendix/colors.html>

    WHITE = {RichTheme.PIE: PieColor.WHITE, RichTheme.ANSI: 'white'}
    BLACK = {RichTheme.PIE: PieColor.BLACK, RichTheme.ANSI: 'black'}
    GREEN = {RichTheme.PIE: PieColor.GREEN, RichTheme.ANSI: 'green'}
    ORANGE = {RichTheme.PIE: PieColor.ORANGE, RichTheme.ANSI: 'yellow'}
    YELLOW = {RichTheme.PIE: PieColor.YELLOW, RichTheme.ANSI: 'bright_yellow'}
    BLUE = {RichTheme.PIE: PieColor.BLUE, RichTheme.ANSI: 'blue'}
    PINK = {RichTheme.PIE: PieColor.PINK, RichTheme.ANSI: 'bright_magenta'}
    PURPLE = {RichTheme.PIE: PieColor.PURPLE, RichTheme.ANSI: 'magenta'}
    RED = {RichTheme.PIE: PieColor.RED, RichTheme.ANSI: 'red'}
    AQUA = {RichTheme.PIE: PieColor.AQUA, RichTheme.ANSI: 'cyan'}
    GREY = {RichTheme.PIE: PieColor.GREY, RichTheme.ANSI: 'bright_black'}

    def apply_theme(
        self, style: RichTheme, *, style_name: Optional[str] = None
    ) -> str:
        """Apply the given style to a particular value."""
        exposed_color = self.value[style]
        if style is RichTheme.PIE:
            assert style_name is not None
            shade = PIE_STYLE_TO_SHADE[PieStyle(style_name)]
            return get_color(exposed_color, shade)
        else:
            return exposed_color


@dataclass
class _StyledRichColor:
    color: RichColor
    styles: List[str] = field(default_factory=list)


class _RichColorCaster(dict):
    """
    Translate RichColor to a regular string on the attribute access
    phase.
    """

    def _translate(self, key: Any) -> Any:
        if isinstance(key, RichColor):
            return key.name.lower()
        else:
            return key

    def __getitem__(self, key: Any) -> Any:
        return super().__getitem__(self._translate(key))

    def get(self, key: Any) -> Any:
        return super().get(self._translate(key))


def make_rich_theme_from_style(style_name: Optional[str] = None) -> 'Theme':
    from rich.style import Style
    from rich.theme import Theme
    from httpie.output.ui.palette.custom_styles import RICH_CUSTOM_STYLES

    rich_theme = RichTheme.from_style_name(style_name)

    theme = Theme()
    for color, color_set in ChainMap(
        RichColor.__members__, RICH_CUSTOM_STYLES
    ).items():
        if isinstance(color_set, _StyledRichColor):
            properties = dict.fromkeys(color_set.styles, True)
            color_set = color_set.color
        else:
            properties = {}

        theme.styles[color.lower()] = Style(
            color=color_set.apply_theme(rich_theme, style_name=style_name),
            **properties,
        )

    # E.g translate RichColor.BLUE into blue on key access
    theme.styles = _RichColorCaster(theme.styles)
    return theme
