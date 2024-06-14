from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from httpie.context import Environment


if TYPE_CHECKING:
    from rich.console import Console


@dataclass
class BaseProgressDisplay:
    env: Environment
    total_size: Optional[float]
    resumed_from: int
    description: str
    summary_suffix: str

    def start(self):
        raise NotImplementedError

    def update(self, steps: float):
        raise NotImplementedError

    def stop(self, time_spent: float):
        raise NotImplementedError

    @property
    def console(self) -> 'Console':
        """Returns the default console to be used with displays (stderr)."""
        return self.env.rich_error_console

    def _print_summary(
        self, is_finished: bool, observed_steps: int, time_spent: float
    ):
        from rich import filesize
        if is_finished:
            verb = 'Done'
        else:
            verb = 'Interrupted'
        total_size = filesize.decimal(observed_steps)
        # noinspection PyTypeChecker
        avg_speed = filesize.decimal(observed_steps / time_spent)
        minutes, seconds = divmod(time_spent, 60)
        hours, minutes = divmod(int(minutes), 60)
        if hours:
            total_time = f'{hours:d}:{minutes:02d}:{seconds:0.5f}'
        else:
            total_time = f'{minutes:02d}:{seconds:0.5f}'
        self.console.print(
            f'[progress.description]{verb}. {total_size} in {total_time} ({avg_speed}/s){self.summary_suffix}'
        )


class DummyProgressDisplay(BaseProgressDisplay):
    """
    A dummy display object to be used when the progress bars,
    spinners etc. are disabled globally (or during tests).
    """

    def start(self):
        pass

    def update(self, steps: float):
        pass

    def stop(self, time_spent: float):
        pass


class ProgressDisplayNoTotal(BaseProgressDisplay):
    observed = 0
    status = None

    def start(self) -> None:
        self.observed = self.resumed_from
        self.description = (
            f'[progress.description]{self.description}[/progress.description]'
        )
        self.status = self.console.status(self.description, spinner='line')
        self.status.start()

    def update(self, steps: int) -> None:
        from rich import filesize
        self.observed += steps
        observed_amount, observed_unit = filesize.decimal(self.observed).split()
        msg = f'{self.description} [progress.download]{observed_amount}/? {observed_unit}[/progress.download]'
        self.status.update(status=msg)

    def stop(self, time_spent: float) -> None:
        self.status.stop()
        self.console.print(self.description)
        if time_spent:
            self._print_summary(
                is_finished=True,
                observed_steps=self.observed,
                time_spent=time_spent,
            )


class ProgressDisplayFull(BaseProgressDisplay):
    progress_bar = None
    transfer_task = None

    def start(self) -> None:
        from rich.progress import (
            Progress,
            BarColumn,
            DownloadColumn,
            TimeRemainingColumn,
            TransferSpeedColumn,
        )
        assert self.total_size is not None
        self.console.print(f'[progress.description]{self.description}')
        self.progress_bar = Progress(
            '[',
            BarColumn(),
            ']',
            '[progress.percentage]{task.percentage:>3.0f}%',
            '(',
            DownloadColumn(),
            ')',
            TimeRemainingColumn(),
            TransferSpeedColumn(),
            console=self.console,
            transient=True,
        )
        self.progress_bar.start()
        self.transfer_task = self.progress_bar.add_task(
            description=self.description,
            completed=self.resumed_from,
            total=self.total_size,
        )

    def update(self, steps: float) -> None:
        self.progress_bar.advance(self.transfer_task, steps)

    def stop(self, time_spent: Optional[float]) -> None:
        self.progress_bar.stop()

        if time_spent:
            [task] = self.progress_bar.tasks
            self._print_summary(
                is_finished=task.finished,
                observed_steps=task.completed,
                time_spent=time_spent,
            )
