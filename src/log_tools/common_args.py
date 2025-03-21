import typer
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from typing import Annotated

load_dotenv()

LogPathOpt = Annotated[Path, typer.Argument(help="Path to the log file(s) to parse")]
StartDateArg = Annotated[datetime, typer.Option(help="First date/time from which to return logs")]
EndDateArg = Annotated[datetime, typer.Option(help="Last date/time from which to return logs")]
MaxLinesArg = Annotated[int, typer.Option(help="Max number of lines to seek backwards")]
TimeFieldArg = Annotated[str, typer.Option(help="Structured log field to parse timestamps from", envvar="TIME_FIELD")]