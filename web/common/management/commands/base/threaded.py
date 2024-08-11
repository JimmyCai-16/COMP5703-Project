import abc
import multiprocessing
import signal
import threading
import time
from abc import ABC
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from math import ceil

from django.core.management import BaseCommand, call_command
from typing import Union

from common.utils.common import ANSI


def optimize_workers_and_batch_size(total_size, batch_size, workers=10):
    """Attempts to optimize the number of workers and batch size based off the input argument values.

    Parameters
    ----------
    total_size : int
        Total size of collection
    batch_size : int
        The size of an individual batch
    workers : int

    Returns
    -------
    Tuple[int, int]
        (workers, batch_size, num_batches)
    """
    record_diff = batch_size / total_size

    if batch_size > total_size or record_diff > 0.5:
        workers = 1
        batch_size = batch_size
    else:
        workers = min(workers, total_size)
        batch_size = min(round(total_size / workers), batch_size)
    num_batches = ceil(total_size / batch_size)
    return workers, batch_size, num_batches


class AbstractProgressCommand(BaseCommand, ABC):
    """Base class for timing command runtime with progress bar."""

    def __init__(self):
        super().__init__()
        self.interrupted = False
        self._start_time = time.time()
        self._progress_thread = None

        signal.signal(signal.SIGINT, self.handle_interrupt)

    @property
    @abc.abstractmethod
    def progress(self) -> Union[int, float]:
        """Total progress made towards completion. Subclass must implement this method."""
        raise NotImplementedError()

    @progress.setter
    @abc.abstractmethod
    def progress(self, value: Union[int, float]):
        """Total progress made towards completion. Subclass must implement this method."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def length(self) -> int:
        """Total size of the process (e.g., number of items in a queryset). Subclass must implement this method."""
        raise NotImplementedError()

    @length.setter
    @abc.abstractmethod
    def length(self, value: int):
        """Total size of the process. Subclass must implement this method."""
        raise NotImplementedError()

    @property
    def start_time(self):
        """Return the start time in seconds. Fractions of a second may be present if the system clock provides them."""
        return self._start_time

    @property
    def now(self) -> float:
        """Return the current time in seconds since the Epoch. Fractions of a second may be present if the system
        clock provides them."""
        return time.time()

    @property
    def elapsed(self):
        """Returns the elapsed duration of the timer in seconds. Fractions of a second may be present if the system
        clock provides them."""
        return self.now - self.start_time

    @property
    def elapsed_str(self):
        """Formatted elapsed time as `H:M:S`."""
        return time.strftime("%H:%M:%S", time.gmtime(self.elapsed))

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def print_progress_bar(self, current, total, length=10, start_c='|', end_c='-'):
        """Prints the progress of a timer given a current item and the total number of items."""
        try:
            progress_percent = self.progress / self.length
        except ZeroDivisionError:
            progress_percent = 0

        done_str = f'{start_c}' * int(round(length * progress_percent))
        remain_str = f'{end_c}' * (length - len(done_str))
        time_str = self.elapsed_str

        self.stdout.write(f'\r{ANSI.HIDE_CURSOR}[{time_str}][{ANSI.GREEN}{done_str}{ANSI.RESET}{remain_str}] {current}/{total}', ending='\r')
        self.stdout.flush()

    def progress_target(self):
        """Continuously updates the progress bar until it has been completed. Use this as a thread target.

        Usage:

        progress_thread = threading.Thread(target=self.progress_target)
        progress_thread.start()
        """
        progress_bar_lock = threading.Lock()

        # While there remains part of the process
        while self.progress < self.length and not self.interrupted:
            with progress_bar_lock:
                self.print_progress_bar(self.progress, self.length)

            time.sleep(0.1)

        # Display a completed progress bar, primarily because the previous bar may not 'complete' due to race conditions.
        if not self.interrupted:
            self.print_progress_bar(self.progress, self.length)

    def handle_interrupt(self, signum, frame):
        self.interrupted = True

    @abc.abstractmethod
    def handle(self, *args, **options):
        raise NotImplementedError()


class AbstractThreadedCommand(AbstractProgressCommand, ABC):
    @property
    def workers(self) -> int:
        """Number of workers. Subclasses must implement this method."""
        return self._workers

    @workers.setter
    def workers(self, value: int):
        """Number of workers."""
        raise ValueError("Unable to modify number of workers after instantiation.")

    @property
    @abc.abstractmethod
    def size(self) -> int:
        """Size of individual batches. Subclasses must implement this method."""
        raise NotImplementedError()

    @size.setter
    def size(self, value: int):
        """Size of individual batches. Subclasses must implement this method."""
        raise NotImplementedError()

    @property
    def cpu_count(self):
        """Return the number of CPUs in the system.

        This number is not equivalent to the number of CPUs the current process can use.
        """
        return multiprocessing.cpu_count()

    @property
    def count(self) -> int:
        """Rounded up number of individual batches."""
        return ceil(self.length / self.size)

    def __init__(self):
        super().__init__()
        self._workers = 10
        self._hyper_threading = False
        self._optimize = True

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--workers', '-w', type=int, default=self.workers, help='The maximum number of workers.')
        parser.add_argument('--size', '-s', type=int, default=self.size, help='The maximum batch size.')
        parser.add_argument('--hyper_threading', '-ht', type=bool, default=self._hyper_threading, help='Enable hyper-threading, number of threads can exceed the number of CPU cores.')
        parser.add_argument('--optimize', '-o', type=bool, default=True, help='Optimizes worker and batch numbers if True.')

    def optimize_parameters(self):
        """Adjusts the workers and batch size to assist in lowering the overhead."""
        record_diff = self.size / self.length

        if self.size > self.length or record_diff > 0.5:
            self._workers = 1
        else:
            self._workers = min(self.workers, self.length)
            self.size = min(round(self.length / self.workers), self.size)

    def handle(self, *args, **options):
        self._workers = options['workers']
        self.size = options['size']

        # Perform user defined setup
        self.setup(*args, **options)

        if options['optimize']:
            self.optimize_parameters()

        futures = []
        done_futures = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Start the progress bar thread
            progress_thread = threading.Thread(target=self.progress_target)
            progress_thread.start()

            # Initialize all the batches ready for work.
            for n in range(self.count):
                future = executor.submit(self.thread, n, *args, **options)
                futures.append(future)

            # Wait for all futures to complete or until interrupted
            for future in as_completed(futures):
                done_futures.append(future)
                if self.interrupted:
                    break

            # Cancel any remaining futures
            for future in futures:
                if future not in done_futures:
                    future.cancel()

            if self.interrupted:
                self.stdout.write(self.style.SUCCESS(f"Command exited early due to keyboard interrupt.{ANSI.SHOW_CURSOR}"))
                return

            # Wait for progress bar to finish, it will finish if interrupted as it's in the main loop so this won't
            # pose an issue.
            progress_thread.join()

        # Perform user defined teardown
        self.teardown(*args, **options)

        # All batches completed without interruption
        self.stdout.write(f"{ANSI.SHOW_CURSOR}")

    def setup(self, *args, **options):
        """Setup before threads have been initialized. Subclasses must implement this method."""
        pass

    def teardown(self, *args, **options):
        """Teardown after all threads have been terminated. Subclasses must implement this method."""
        pass

    @abc.abstractmethod
    def thread(self, n, *args, **options):
        """The actual logic of a thread. Subclasses must implement this method."""
        raise NotImplementedError()


class BaseMultiCommand(BaseCommand, ABC):
    """Base Class for calling multiple commands"""

    @property
    @abc.abstractmethod
    def commands(self) -> list:
        """Returns a list of commands to be run. Subclasses must implement this method."""
        raise NotImplementedError()

    def handle(self, *args, **options):
        # List of command classes to run
        if not self.commands:
            raise NotImplementedError(f"{self.__class__} must specify at least one command.")

        for command in self.commands:
            # Use call_command to run the command by class name
            call_command(command, *args, **options)


class BaseThreadedMultiCommand(BaseCommand, ABC):
    """Base Class for calling multiple commands. Threaded parameters are passed to sub-commands."""
    @property
    @abc.abstractmethod
    def commands(self) -> list:
        """Returns a list of commands to be run. Subclasses must implement this method."""
        raise NotImplementedError()

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--workers', '-w', type=int, default=10, help='The maximum number of workers.')
        parser.add_argument('--size', '-s', type=int, default=100, help='The maximum batch size.')
        parser.add_argument('--hyper_threading', '-ht', type=bool, default=False, help='Enable hyper-threading, number of threads can exceed the number of CPU cores.')
        parser.add_argument('--optimize', '-o', type=bool, default=True, help='Optimizes worker and batch numbers if True.')

    def handle(self, *args, **options):
        # List of command classes to run
        if not self.commands:
            raise NotImplementedError(f"{self.__class__} must specify at least one command.")

        for command in self.commands:
            # Use call_command to run the command by class name
            call_command(command, *args, **options)


class BaseThreadedScraperCommand(AbstractThreadedCommand, ABC):
    help = (
        "Scrapes some URL into a database model. "
        "Many-to-many relationships must still be handled manually."
    )

    url = ''
    urls = []
    model = None
    field_map = {}
    unique_fields = []

    def __init__(self):
        super().__init__()
        self._length = 0
        self._batch_size = 0
        self._progress = 0

    @property
    def length(self) -> int:
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    @property
    def size(self) -> int:
        return self._batch_size

    @size.setter
    def size(self, value):
        self._batch_size = value

    @property
    def progress(self) -> int:
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--url', '-u', type=str, default=self.url, help='URL path of target.')

    def handle(self, *args, **options):
        # Handle for multiple urls if we have them
        if self.urls and not self.url:
            # Return if interrupted
            if self.interrupted:
                return

            # Update URL each time, this will cause the class to operate for multiple different servers.
            for url in self.urls:
                self.url = url
                super().handle(*args, **options)
        else:
            super().handle(*args, **options)