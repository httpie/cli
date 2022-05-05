from collections import ChainMap
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from rich.theme import Theme

from httpie.output.ui.palette import GenericColor, PieStyle, Styles, ColorString, _StyledGenericColor  # noqa

RICH_BOLD = ColorString('bold')

# Rich-specific color code declarations
# <https://github.com/Textualize/rich/blob/fcd684dd3a482977cab620e71ccaebb94bf13ac9/rich/default_styles.py>
CUSTOM_STYLES = {
    'progress.description': RICH_BOLD | GenericColor.WHITE,
    'progress.data.speed': RICH_BOLD | GenericColor.GREEN,
    'progress.percentage': RICH_BOLD | GenericColor.AQUA,
    'progress.download': RICH_BOLD | GenericColor.AQUA,
    'progress.remaining': RICH_BOLD | GenericColor.ORANGE,
    'bar.complete': RICH_BOLD | GenericColor.PURPLE,
    'bar.finished': RICH_BOLD | GenericColor.GREEN,
    'bar.pulse': RICH_BOLD | GenericColor.PURPLE,
    'option': RICH_BOLD | GenericColor.PINK,
}


class _GenericColorCaster(dict):
    """
    Translate GenericColor to a regular string on the attribute access
    phase.
    """

    def _translate(self, key: Any) -> Any:
        if isinstance(key, GenericColor):
            return key.name.lower()
        else:
            return key

    def __getitem__(self, key: Any) -> Any:
        return super().__getitem__(self._translate(key))

    def get(self, key: Any) -> Any:
        return super().get(self._translate(key))


def _make_rich_color_theme(style_name: Optional[str] = None) -> 'Theme':
    from rich.style import Style
    from rich.theme import Theme

    try:
        PieStyle(style_name)
    except ValueError:
        style = Styles.ANSI
    else:
        style = Styles.PIE

    theme = Theme()
    for color, color_set in ChainMap(
        GenericColor.__members__, CUSTOM_STYLES
    ).items():
        if isinstance(color_set, _StyledGenericColor):
            properties = dict.fromkeys(color_set.styles, True)
            color_set = color_set.color
        else:
            properties = {}

        theme.styles[color.lower()] = Style(
            color=color_set.apply_style(style, style_name=style_name),
            **properties,
        )

    # E.g translate GenericColor.BLUE into blue on key access
    theme.styles = _GenericColorCaster(theme.styles)
    return theme
