import typer
from datetime import datetime
from . import common_args as ca
from .file_utils import read_file_reverse
from .log_tools import dt_in_range_fix_tz
from .log_utils import safe_parse_line
from collections import defaultdict

class MissingNumberTracker:
    missing_ranges: list[tuple[int, int]] = []
    min_seen: int = None
    max_seen: int = None

    def add_number(self, num: int):
        if self.min_seen is None or self.max_seen is None:
            self.min_seen = self.max_seen = num
            return

        if num > self.max_seen:
            # Add missing range if needed between previous max and new num
            if num > self.max_seen + 1:
                self._insert_range(self.max_seen + 1, num - 1)
            self.max_seen = num
        elif num < self.min_seen:
            # Add missing range if needed between new num and previous min
            if num < self.min_seen - 1:
                self._insert_range(num + 1, self.min_seen - 1)
            self.min_seen = num
        else:
            # Remove the number from existing ranges
            self._remove_from_ranges(num)

    def _insert_range(self, start: int, end: int):
        if start > end:
            return
        new_ranges = []
        inserted = False
        for s, e in self.missing_ranges:
            if not inserted and end < s:
                new_ranges.append((start, end))
                inserted = True
            new_ranges.append((s, e))
        if not inserted:
            new_ranges.append((start, end))
        self.missing_ranges = self._merge_ranges(new_ranges)

    def _remove_from_ranges(self, num:int):
        new_ranges = []
        for start, end in self.missing_ranges:
            if num < start or num > end:
                new_ranges.append((start, end))
            elif start == end == num:
                continue  # Remove the range
            elif start == num:
                new_ranges.append((start + 1, end))
            elif end == num:
                new_ranges.append((start, end - 1))
            else:
                new_ranges.append((start, num - 1))
                new_ranges.append((num + 1, end))
        self.missing_ranges = new_ranges

    def _merge_ranges(self, ranges: list[tuple[int, int]]):
        if not ranges:
            return []
        ranges.sort()
        merged = [ranges[0]]
        for current in ranges[1:]:
            prev_start, prev_end = merged[-1]
            curr_start, curr_end = current
            if prev_end + 1 >= curr_start:
                merged[-1] = (prev_start, max(prev_end, curr_end))
            else:
                merged.append(current)
        return merged

    def get_missing_ranges(self):
        return self.missing_ranges


sequence = typer.Typer(help="Sub-commands to validate log sequence numbers")

@sequence.callback(invoke_without_command=True)
def check_sequence(
    log_path: ca.LogPathOpt,
    start_date: ca.StartDateArg = datetime.min,
    end_date: ca.EndDateArg = datetime.max,
    time_field: ca.TimeFieldArg = 'time',
    max_lines: ca.MaxLinesArg = 0,
):
    """ Given a set of log files containing the special "sequence_info" JSON sub-object:
    {"sequence_info": {"logger_id": "<uuid>", "sequence_no": <int> }}
    return any gaps in the log sequences appearing in that file
    """

    # For each logger, record every log sequence appearing under its logger ID
    logger_ids : dict[str, MissingNumberTracker] = defaultdict(MissingNumberTracker)
    for idx, line in enumerate(read_file_reverse(log_path, chunk_size = 2048*12)):
        parsed, fields = safe_parse_line(line)
        if not parsed:
            continue

        time = datetime.fromisoformat(fields[time_field])
        if dt_in_range_fix_tz(start_date, time, end_date) and fields.get("sequence_info", dict()).get("logger_id"):
            logger_ids[fields["sequence_info"]["logger_id"]].add_number(fields["sequence_info"]["sequence_no"])

        if max_lines and idx >= max_lines:
            break

    # For each logger, compute any gaps in the logger's recorded sequence
    for logger_id, tracker in logger_ids.items():
        logger_result = tracker.get_missing_ranges()
        print(f"{logger_id}: {logger_result}")
