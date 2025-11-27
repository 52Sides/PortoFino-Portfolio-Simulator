import asyncio
from datetime import datetime
from typing import List
import re

from schemas.simulation import ParsedCommandModel

MAX_POSITIONS = 10
MAX_CMD_LENGTH = 500


class CommandValidationError(ValueError):
    pass


def _parse_sync(command: str) -> ParsedCommandModel:
    if not isinstance(command, str) or not command.strip() or len(command) > MAX_CMD_LENGTH:
        raise CommandValidationError("Command must be a non-empty string of max length 500")

    parts = command.strip().split()
    if len(parts) < 3:
        raise CommandValidationError("Invalid format: expected positions and start/end dates")

    start_date_str, end_date_str = parts[-2], parts[-1]

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise CommandValidationError("Invalid date format (expected YYYY-MM-DD)")

    if start_date >= end_date:
        raise CommandValidationError("start_date must be before end_date")

    raw_positions = parts[:-2]
    if len(raw_positions) > MAX_POSITIONS:
        raise CommandValidationError(f"Too many tickers (max {MAX_POSITIONS})")

    position_re = re.compile(r'^([A-Z0-9.-]{1,10})-([LS])-([0-9]{1,3})%$')

    tickers: List[str] = []
    weights: List[float] = []
    sides: List[str] = []
    total_weight = 0.0

    for pos in raw_positions:
        m = position_re.match(pos)
        if not m:
            raise CommandValidationError(f"Invalid position '{pos}', expected format 'TICKER-L-50%'")

        ticker, side, weight_str = m.groups()

        if ticker in tickers:
            raise CommandValidationError(f"Duplicate ticker '{ticker}' not allowed")

        weight = float(weight_str)
        if not (0 < weight <= 100):
            raise CommandValidationError(f"Invalid weight '{weight_str}'")

        tickers.append(ticker)
        weights.append(weight / 100.0)
        sides.append(side)
        total_weight += weight

    if abs(total_weight - 100.0) > 0.01:
        raise CommandValidationError(f"Weights must sum to 100%, got {total_weight:.1f}%")

    return ParsedCommandModel(
        tickers=tickers,
        weights=weights,
        sides=sides,
        start_date=start_date,
        end_date=end_date,
    )


async def safe_command_parse(command: str) -> ParsedCommandModel:
    return await asyncio.to_thread(_parse_sync, command)
