import functools
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# from pandas import DataFrame
from python_log_indenter import IndentedLoggerAdapter

from .settings import conf

_active_loggers = dict()
session_root = Path(conf.dirs.logs) / datetime.now().strftime(r"%y%m%d")


def to_level(level: str | int = 0):
    match level:
        case "debug":
            return logging.DEBUG
        case "info":
            return logging.INFO
        case "warn":
            return logging.WARN
        case "error":
            return logging.ERROR
        case "critical":
            return logging.CRITICAL
        case str():
            try:
                level = int(level)
                return level
            except:
                return 0
        case int():
            return level
        case _:
            return 0


def get_logger(name: str = conf.logger.name):
    try:
        return _active_loggers[name]
    except KeyError:
        pass
    log = logging.getLogger(name)
    if not log.hasHandlers():
        session_root.mkdir(parents=True, exist_ok=True)
        if conf.logger.stream:
            h = logging.StreamHandler(sys.stdout)

            h.setLevel(to_level(conf.logger.stream.level))
            log.addHandler(h)

        if conf.logger.file:
            with open(session_root / "debug.log", "a") as f:
                f.write("\n")
            h = logging.FileHandler(filename=session_root / "debug.log", mode="a")
            h.setLevel(to_level(conf.logger.file.level))
            h.setFormatter(
                logging.Formatter(
                    conf.logger.file.format,
                    style="%",
                    datefmt=conf.logger.file.datefmt,
                )
            )
            log.addHandler(h)

        if conf.logger.tsv:
            h = CustomTsvFileHandler(filename=session_root / "debug.tsv", mode="a")
            h.setLevel(to_level(conf.logger.tsv.level))
            h.setFormatter(
                logging.Formatter(
                    (conf.logger.tsv.format).replace(
                        "%(parent_pid)d",
                        str(os.getppid()),
                    ),
                    style="%",
                    datefmt=conf.logger.tsv.datefmt,
                ),
            )
            log.addHandler(h)

        log.setLevel(logging.DEBUG)
    log = Adapter(log, name=name, spaces=2)
    _active_loggers[name] = log
    return log


class CustomTsvFileHandler(logging.FileHandler):
    def emit(self, record):
        try:
            record.msg = repr(record.msg)
            super().emit(record)
        except Exception:
            self.handleError(record)


class Adapter(IndentedLoggerAdapter):
    def __init__(self, logger, *, name: str, extra=None, auto_add=True, **kwargs):
        if extra is None:
            extra = {}
        extra = extra | dict(name=name, path=session_root / name)
        super().__init__(logger, extra, auto_add, **kwargs)

    def ensure_path(self):
        Path(self.extra.get("path")).mkdir(parents=True, exist_ok=True)

    def process(self, msg, kwargs):
        if isinstance(msg, Exception):
            msg = str("\n").join(
                [
                    line
                    for part in traceback.format_exception(msg)
                    for line in part.splitlines()
                    if len(line) > 0
                ]
            )
        # elif isinstance(msg, DataFrame):
        #     msg = msg.to_string()
        else:
            msg = str(msg)
        return super().process(msg, kwargs)


log = get_logger()


def indent(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        id = uuid4().hex
        log.push(id).add()
        try:
            result = func(*args, **kwargs)
        finally:
            log.pop(id)
        return result

    return wrapper
