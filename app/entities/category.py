"""Category domain exceptions."""


class CategoryNotFoundError(Exception):
    """Exception raised when category is not found."""

    def __init__(self, message: str = 'Category not found') -> None:
        self.message = message
        super().__init__(self.message)


class CategoryMediaNotFoundError(Exception):
    """Exception raised when category media is not found."""

    def __init__(self, message: str = 'Media not found in category gallery') -> None:
        self.message = message
        super().__init__(self.message)
