from httpie.output.ui.palette import * # noqa

# Rich-specific color code declarations
# https://github.com/Textualize/rich/blob/fcd684dd3a482977cab620e71ccaebb94bf13ac9/rich/default_styles.py#L5
CUSTOM_STYLES = {
    'progress.description': 'white',
    'progress.data.speed': 'green',
    'progress.percentage': 'aqua',
    'progress.download': 'aqua',
    'progress.remaining': 'orange',
    'bar.complete': 'purple',
    'bar.finished': 'green',
    'bar.pulse': 'purple',
}

RICH_THEME_PALETTE = COLOR_PALETTE.copy() # noqa
RICH_THEME_PALETTE.update(
    {
        custom_style: RICH_THEME_PALETTE[color]
        for custom_style, color in CUSTOM_STYLES.items()
    }
)
