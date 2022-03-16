from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from httpie.context import Environment

if TYPE_CHECKING:
    from rich.console import Console


@dataclass
class BaseDisplay:
    env: Environment

    def start(
        self, *, total: Optional[float], at: float, description: str
    ) -> None:
        ...

    def update(self, steps: float) -> None:
        ...

    def stop(self) -> None:
        ...

    @property
    def console(self) -> 'Console':
        """Returns the default console to be used with displays (stderr)."""
        return self.env.rich_error_console


class DummyDisplay(BaseDisplay):
    """
    A dummy display object to be used when the progress bars,
    spinners etc. are disabled globally (or during tests).
    """


class StatusDisplay(BaseDisplay):
    def start(
        self, *, total: Optional[float], at: float, description: str
    ) -> None:
        self.observed = at
        self.description = f'[white]{description}[/white]'

        self.status = self.console.status(self.description, spinner='line')
        self.status.start()

    def update(self, steps: float) -> None:
        from rich import filesize

        self.observed += steps

        observed_units = filesize.decimal(self.observed, separator='/? ')
        self.status.update(status=f'{self.description} [progress.download]{observed_units}[/progress.download]')

    def stop(self) -> None:
        self.status.stop()


class ProgressDisplay(BaseDisplay):
    def start(
        self, *, total: Optional[float], at: float, description: str
    ) -> None:
        from rich.progress import (
            Progress,
            BarColumn,
            DownloadColumn,
            TimeRemainingColumn,
            TransferSpeedColumn,
        )

        assert total is not None
        self.progress_bar = Progress(
            '[progress.description]{task.description}',
            BarColumn(),
            '[progress.percentage]{task.percentage:>3.0f}%',
            '(',
            DownloadColumn(),
            ')',
            TimeRemainingColumn(),
            TransferSpeedColumn(),
            console=self.console,
        )
        self.progress_bar.start()
        self.transfer_task = self.progress_bar.add_task(
            description, completed=at, total=total
        )

    def update(self, steps: float) -> None:
        self.progress_bar.advance(self.transfer_task, steps)

    def stop(self) -> None:
        self.progress_bar.stop()
