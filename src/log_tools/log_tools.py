import typer
from typing import Annotated
from datetime import datetime
from pathlib import Path
import pytz
import json
import typing as t
from . import common_args as ca
from .utils import readlines_reverse

filterer = typer.Typer()


def dt_in_range_fix_tz(start_date: datetime, date: datetime, end_date: datetime):
    """
    Check whether a given date falls within a start and stop date, applying the
    date's tz to the range endpoints if they do not yet have them
    """
    start_date = start_date.replace(tzinfo=date.tzinfo)
    end_date = end_date.replace(tzinfo=date.tzinfo)

    return start_date <= date <= end_date

@filterer.callback(invoke_without_command=True)
def filter_logs_by_date(
        log_path: ca.LogPathOpt,
        start_date: ca.StartDateArg = datetime.min,
        end_date: ca.EndDateArg = datetime.max,
        time_field: ca.TimeFieldArg = 'time',
        max_lines: ca.MaxLinesArg = 0,
        filters: Annotated[list[str], typer.Option(help="Key-Value pairs that should appear in the logs")] = []
):
    """ Reference function that parses newline-delimited, JSON formatted 
    logs based on a time range
    """

    # Parse a list of key, value pairs out of filters (assumed to be a list of "key=value" strings)
    # TODO input validation
    filter_list : dict[str, str] = dict(f.split("=") for f in filters)

    # TODO a real implementation of log filtering
    with open(log_path, 'rb') as logf:
        for idx, line in enumerate(readlines_reverse(logf)):
            try:
                fields :dict[str, t.Any]= json.loads(line)
            except json.JSONDecodeError as e:
                print(f"UNABLE TO PARSE LINE: '''\n\t{line}'''")
                continue

            time = datetime.fromisoformat(fields[time_field])
            if dt_in_range_fix_tz(start_date, time, end_date) and all(fields.get(k) == v for k, v in filter_list.items()):
                print(line)

            if max_lines and idx >= max_lines:
                break

