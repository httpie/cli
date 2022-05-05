from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List


PYGMENTS_BRIGHT_BLACK = 'ansibrightblack'

AUTO_STYLE = 'auto'  # Follows terminal ANSI color styles


class Styles(Enum):
    PIE = auto()
    ANSI = auto()


class PieStyle(str, Enum):
    UNIVERSAL = 'pie'
    DARK = 'pie-dark'
    LIGHT = 'pie-light'


PIE_STYLE_TO_SHADE = {
    PieStyle.DARK: '500',
    PieStyle.UNIVERSAL: '600',
    PieStyle.LIGHT: '700',
}
SHADE_TO_PIE_STYLE = {
    shade: style for style, shade in PIE_STYLE_TO_SHADE.items()
}


class ColorString(str):
    def __or__(self, other: str) -> 'ColorString':
        """Combine a style with a property.

        E.g: PieColor.BLUE | BOLD | ITALIC
        """
        if isinstance(other, str):
            # In case of PieColor.BLUE | SOMETHING
            # we just create a new string.
            return ColorString(self + ' ' + other)
        elif isinstance(other, GenericColor):
            # If we see a GenericColor, then we'll wrap it
            # in with the desired property in a different class.
            return _StyledGenericColor(other, styles=self.split())
        elif isinstance(other, _StyledGenericColor):
            # And if it is already wrapped, we'll just extend the
            # list of properties.
            other.styles.extend(self.split())
            return other
        else:
            return NotImplemented


class PieColor(ColorString, Enum):
    """Styles that are available only in Pie themes."""

    PRIMARY = 'primary'
    SECONDARY = 'secondary'

    WHITE = 'white'
    BLACK = 'black'
    GREY = 'grey'
    AQUA = 'aqua'
    PURPLE = 'purple'
    ORANGE = 'orange'
    RED = 'red'
    BLUE = 'blue'
    PINK = 'pink'
    GREEN = 'green'
    YELLOW = 'yellow'


class GenericColor(Enum):
    """Generic colors that are safe to use everywhere."""

    # <https://rich.readthedocs.io/en/stable/appendix/colors.html>

    WHITE = {Styles.PIE: PieColor.WHITE, Styles.ANSI: 'white'}
    BLACK = {Styles.PIE: PieColor.BLACK, Styles.ANSI: 'black'}
    GREEN = {Styles.PIE: PieColor.GREEN, Styles.ANSI: 'green'}
    ORANGE = {Styles.PIE: PieColor.ORANGE, Styles.ANSI: 'yellow'}
    YELLOW = {Styles.PIE: PieColor.YELLOW, Styles.ANSI: 'bright_yellow'}
    BLUE = {Styles.PIE: PieColor.BLUE, Styles.ANSI: 'blue'}
    PINK = {Styles.PIE: PieColor.PINK, Styles.ANSI: 'bright_magenta'}
    PURPLE = {Styles.PIE: PieColor.PURPLE, Styles.ANSI: 'magenta'}
    RED = {Styles.PIE: PieColor.RED, Styles.ANSI: 'red'}
    AQUA = {Styles.PIE: PieColor.AQUA, Styles.ANSI: 'cyan'}
    GREY = {Styles.PIE: PieColor.GREY, Styles.ANSI: 'bright_black'}

    def apply_style(
        self, style: Styles, *, style_name: Optional[str] = None
    ) -> str:
        """Apply the given style to a particular value."""
        exposed_color = self.value[style]
        if style is Styles.PIE:
            assert style_name is not None
            shade = PIE_STYLE_TO_SHADE[PieStyle(style_name)]
            return get_color(exposed_color, shade)
        else:
            return exposed_color


@dataclass
class _StyledGenericColor:
    color: 'GenericColor'
    styles: List[str] = field(default_factory=list)


# noinspection PyDictCreation
COLOR_PALETTE = {
    # Copy the brand palette
    PieColor.WHITE: '#F5F5F0',
    PieColor.BLACK: '#1C1818',
    PieColor.GREY: {
        '50': '#F5F5F0',
        '100': '#EDEDEB',
        '200': '#D1D1CF',
        '300': '#B5B5B2',
        '400': '#999999',
        '500': '#7D7D7D',
        '600': '#666663',
        '700': '#4F4D4D',
        '800': '#363636',
        '900': '#1C1818',
        'DEFAULT': '#7D7D7D',
    },
    PieColor.AQUA: {
        '50': '#E8F0F5',
        '100': '#D6E3ED',
        '200': '#C4D9E5',
        '300': '#B0CCDE',
        '400': '#9EBFD6',
        '500': '#8CB4CD',
        '600': '#7A9EB5',
        '700': '#698799',
        '800': '#597082',
        '900': '#455966',
        'DEFAULT': '#8CB4CD',
    },
    PieColor.PURPLE: {
        '50': '#F0E0FC',
        '100': '#E3C7FA',
        '200': '#D9ADF7',
        '300': '#CC96F5',
        '400': '#BF7DF2',
        '500': '#B464F0',
        '600': '#9E54D6',
        '700': '#8745BA',
        '800': '#70389E',
        '900': '#5C2982',
        'DEFAULT': '#B464F0',
    },
    PieColor.ORANGE: {
        '50': '#FFEDDB',
        '100': '#FFDEBF',
        '200': '#FFCFA3',
        '300': '#FFBF87',
        '400': '#FFB06B',
        '500': '#FFA24E',
        '600': '#F2913D',
        '700': '#E3822B',
        '800': '#D6701C',
        '900': '#C75E0A',
        'DEFAULT': '#FFA24E',
    },
    PieColor.RED: {
        '50': '#FFE0DE',
        '100': '#FFC7C4',
        '200': '#FFB0AB',
        '300': '#FF968F',
        '400': '#FF8075',
        '500': '#FF665B',
        '600': '#E34F45',
        '700': '#C7382E',
        '800': '#AD2117',
        '900': '#910A00',
        'DEFAULT': '#FF665B',
    },
    PieColor.BLUE: {
        '50': '#DBE3FA',
        '100': '#BFCFF5',
        '200': '#A1B8F2',
        '300': '#85A3ED',
        '400': '#698FEB',
        '500': '#4B78E6',
        '600': '#426BD1',
        '700': '#3B5EBA',
        '800': '#3354A6',
        '900': '#2B478F',
        'DEFAULT': '#4B78E6',
    },
    PieColor.PINK: {
        '50': '#FFEBFF',
        '100': '#FCDBFC',
        '200': '#FCCCFC',
        '300': '#FCBAFC',
        '400': '#FAABFA',
        '500': '#FA9BFA',
        '600': '#DE85DE',
        '700': '#C26EC2',
        '800': '#A854A6',
        '900': '#8C3D8A',
        'DEFAULT': '#FA9BFA',
    },
    PieColor.GREEN: {
        '50': '#E3F7E8',
        '100': '#CCF2D6',
        '200': '#B5EDC4',
        '300': '#A1E8B0',
        '400': '#8AE09E',
        '500': '#73DC8C',
        '600': '#63C27A',
        '700': '#52AB66',
        '800': '#429154',
        '900': '#307842',
        'DEFAULT': '#73DC8C',
    },
    PieColor.YELLOW: {
        '50': '#F7F7DB',
        '100': '#F2F2BF',
        '200': '#EDEDA6',
        '300': '#E5E88A',
        '400': '#E0E36E',
        '500': '#DBDE52',
        '600': '#CCCC3D',
        '700': '#BABA29',
        '800': '#ABA614',
        '900': '#999400',
        'DEFAULT': '#DBDE52',
    },
}
COLOR_PALETTE.update(
    {
        # Terminal-specific palette customizations.
        PieColor.GREY: {
            # Grey is the same no matter shade for the colors
            shade: COLOR_PALETTE[PieColor.GREY]['500']
            for shade in COLOR_PALETTE[PieColor.GREY].keys()
        },
        PieColor.PRIMARY: {
            '700': COLOR_PALETTE[PieColor.BLACK],
            '600': PYGMENTS_BRIGHT_BLACK,
            '500': COLOR_PALETTE[PieColor.WHITE],
        },
        PieColor.SECONDARY: {
            '700': '#37523C',
            '600': '#6c6969',
            '500': '#6c6969',
        },
    }
)


def boldify(color: PieColor) -> str:
    return f'bold {color}'


# noinspection PyDefaultArgument
def get_color(
    color: PieColor, shade: str, *, palette=COLOR_PALETTE
) -> Optional[str]:
    if color not in palette:
        return None
    color_code = palette[color]
    if isinstance(color_code, dict) and shade in color_code:
        return color_code[shade]
    else:
        return color_code
