from httpie.output.ui.palette.rich import RichColor
from httpie.output.ui.palette.utils import ColorString

RICH_BOLD = ColorString('bold')

# Rich-specific color code declarations
# <https://github.com/Textualize/rich/blob/fcd684dd3a482977cab620e71ccaebb94bf13ac9/rich/default_styles.py>
RICH_CUSTOM_STYLES = {
    'progress.description': RICH_BOLD | RichColor.WHITE,
    'progress.data.speed': RICH_BOLD | RichColor.GREEN,
    'progress.percentage': RICH_BOLD | RichColor.AQUA,
    'progress.download': RICH_BOLD | RichColor.AQUA,
    'progress.remaining': RICH_BOLD | RichColor.ORANGE,
    'bar.complete': RICH_BOLD | RichColor.PURPLE,
    'bar.finished': RICH_BOLD | RichColor.GREEN,
    'bar.pulse': RICH_BOLD | RichColor.PURPLE,
    'option': RICH_BOLD | RichColor.PINK,
}
