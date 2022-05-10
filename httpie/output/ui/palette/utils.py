class ColorString(str):
    def __or__(self, other: str) -> 'ColorString':
        """Combine a style with a property.

        E.g: PieColor.BLUE | BOLD | ITALIC
        """
        from httpie.output.ui.palette.rich import RichColor, _StyledRichColor

        if isinstance(other, str):
            # In case of PieColor.BLUE | SOMETHING
            # we just create a new string.
            return ColorString(self + ' ' + other)
        elif isinstance(other, RichColor):
            # If we see a GenericColor, then we'll wrap it
            # in with the desired property in a different class.
            return _StyledRichColor(other, styles=self.split())
        elif isinstance(other, _StyledRichColor):
            # And if it is already wrapped, we'll just extend the
            # list of properties.
            other.styles.extend(self.split())
            return other
        else:
            return NotImplemented
