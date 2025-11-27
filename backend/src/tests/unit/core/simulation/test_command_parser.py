import pytest
from datetime import date

from core.simulation.command_parser import safe_command_parse, CommandValidationError
from schemas.simulation import ParsedCommandModel


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_command_parse_success():
    cmd = "TSLA-L-50% AAPL-S-50% 2020-01-01 2021-01-01"
    parsed: ParsedCommandModel = await safe_command_parse(cmd)
    assert parsed.tickers == ["TSLA", "AAPL"]
    assert parsed.weights == [0.5, 0.5]
    assert parsed.sides == ["L", "S"]
    assert parsed.start_date == date(2020, 1, 1)
    assert parsed.end_date == date(2021, 1, 1)


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_cmd", ["", "   ", None])
async def test_safe_command_parse_empty(invalid_cmd):
    with pytest.raises(CommandValidationError):
        await safe_command_parse(invalid_cmd)


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_cmd", [
    "TSLA-50% AAPL-S-50% 2020-01-01 2021-01-01",
    "TSLA-L-500% AAPL-S-50% 2020-01-01 2021-01-01",
    "TSLA-L-0% AAPL-S-100% 2020-01-01 2021-01-01",
    "TSLA-L-50 AAPL-S-50% 2020-01-01 2021-01-01"
])
async def test_safe_command_parse_invalid_format(invalid_cmd):
    with pytest.raises(CommandValidationError):
        await safe_command_parse(invalid_cmd)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_command_parse_duplicate_ticker():
    cmd = "TSLA-L-50% TSLA-S-50% 2020-01-01 2021-01-01"
    with pytest.raises(CommandValidationError):
        await safe_command_parse(cmd)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_command_parse_weights_sum_error():
    cmd = "TSLA-L-60% AAPL-S-50% 2020-01-01 2021-01-01"
    with pytest.raises(CommandValidationError):
        await safe_command_parse(cmd)


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("cmd", [
    "TSLA-L-50% AAPL-S-50% 2021-01-01 2020-01-01",
    "TSLA-L-50% AAPL-S-50% 2020-13-01 2021-01-01",
    "TSLA-L-50% AAPL-S-50% 2020-01-32 2021-01-01",
])
async def test_safe_command_parse_invalid_dates(cmd):
    with pytest.raises(CommandValidationError):
        await safe_command_parse(cmd)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_command_parse_max_positions():
    positions = " ".join([f"T{i}-L-10%" for i in range(11)])
    cmd = f"{positions} 2020-01-01 2021-01-01"
    with pytest.raises(CommandValidationError):
        await safe_command_parse(cmd)
