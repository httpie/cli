from collections import ChainMap
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from rich.theme import Theme

from httpie.output.ui.palette import GenericColor, PieStyle, Styles  # noqa

# Rich-specific color code declarations
# <https://github.com/Textualize/rich/blob/fcd684dd3a482977cab620e71ccaebb94bf13ac9/rich/default_styles.py>
CUSTOM_STYLES = {
    'progress.description': GenericColor.WHITE,
    'progress.data.speed': GenericColor.GREEN,
    'progress.percentage': GenericColor.AQUA,
    'progress.download': GenericColor.AQUA,
    'progress.remaining': GenericColor.ORANGE,
    'bar.complete': GenericColor.PURPLE,
    'bar.finished': GenericColor.GREEN,
    'bar.pulse': GenericColor.PURPLE,
    'option': GenericColor.PINK,
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


def _make_rich_color_theme(style_name: Optional[str]) -> 'Theme':
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
        theme.styles[color.lower()] = Style(
            color=color_set.apply_style(style, style_name=style_name),
            bold=style is Styles.PIE,
        )

    # E.g translate GenericColor.BLUE into blue on key access
    theme.styles = _GenericColorCaster(theme.styles)
    return theme
