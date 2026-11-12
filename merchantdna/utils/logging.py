"""One-line logger with timestamps, shared by all pipeline steps."""
from __future__ import annotations

import logging
import time


def get_logger(name: str) -> logging.Logger:
    """Return a logger that prints `HH:MM:SS name | message`."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s | %(message)s",
                        datefmt="%H:%M:%S")
    return logging.getLogger(name)


class Timer:
    """Context manager that logs how long a block took."""

    def __init__(self, log: logging.Logger, what: str) -> None:
        self.log, self.what = log, what

    def __enter__(self) -> "Timer":
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.log.info("%s took %.1fs", self.what, time.perf_counter() - self.t0)
