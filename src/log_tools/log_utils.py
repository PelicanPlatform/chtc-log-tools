import json
import typing


def safe_parse_line(line: str) -> tuple[bool, dict[str, typing.Any]]:
    """ Attempt to parse a line as JSON, logging an error and returning false
    if parsing fails
    """
    if not line:
        return False, {}
    try: 
        return True, json.loads(line)
    except json.JSONDecodeError as e:
        print(f"Unable to JSON-decode formatted line '{line}'")
        return False, {}