# Copy the brand palette
from typing import Optional

COLOR_PALETTE = {
    'transparent': 'transparent',
    'current': 'currentColor',
    'white': '#F5F5F0',
    'black': '#1C1818',
    'grey': {
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
    'aqua': {
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
    'purple': {
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
    'orange': {
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
    'red': {
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
    'blue': {
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
    'pink': {
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
    'green': {
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
    'yellow': {
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

# Grey is the same no matter shade for the colors
COLOR_PALETTE['grey'] = {
    shade: COLOR_PALETTE['grey']['500'] for shade in COLOR_PALETTE['grey'].keys()
}

COLOR_PALETTE['primary'] = {
    '700': COLOR_PALETTE['black'],
    '600': 'ansibrightblack',
    '500': COLOR_PALETTE['white'],
}

COLOR_PALETTE['secondary'] = {'700': '#37523C', '600': '#6c6969', '500': '#6c6969'}

SHADE_NAMES = {
    '500': 'pie-dark',
    '600': 'pie',
    '700': 'pie-light'
}

SHADES = [
    '50',
    *map(str, range(100, 1000, 100))
]


def get_color(color: str, shade: str) -> Optional[str]:
    if color not in COLOR_PALETTE:
        return None

    color_code = COLOR_PALETTE[color]
    if isinstance(color_code, dict) and shade in color_code:
        return color_code[shade]
    else:
        return color_code
