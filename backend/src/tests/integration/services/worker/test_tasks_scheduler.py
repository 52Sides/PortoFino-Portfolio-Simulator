import os
import time
import pytest
from pathlib import Path

from unittest.mock import MagicMock, patch

from services.worker.tasks.scheduler import (
    vacuum_analyze_task,
    cluster_asset_prices_task,
    cleanup_old_report_files_task,
)


@pytest.mark.integration
def test_vacuum_analyze_task_logs_exception():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = RuntimeError("boom")
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn

    with patch("services.worker.tasks.scheduler.pg_conn", return_value=mock_conn), \
         patch("services.worker.tasks.scheduler.logger") as mock_logger:

        vacuum_analyze_task()

    assert mock_logger.exception.called


@pytest.mark.integration
def test_cluster_asset_prices_task_logs_exception():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = RuntimeError("fail")
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn

    with patch("services.worker.tasks.scheduler.pg_conn", return_value=mock_conn), \
         patch("services.worker.tasks.scheduler.logger") as mock_logger:

        cluster_asset_prices_task()

    assert mock_logger.exception.called


@pytest.mark.integration
def test_cleanup_old_report_files_handles_unlink_error(tmp_path, monkeypatch):
    monkeypatch.setattr("core.report.xls_generator.REPORTS_DIR", tmp_path)

    bad_file = tmp_path / "report_001.xls"
    bad_file.write_text("test")
    os.utime(bad_file, (time.time() - 9 * 86400,) * 2)

    def fail_unlink(self):
        raise RuntimeError("cannot delete")
    monkeypatch.setattr(type(bad_file), "unlink", fail_unlink)

    with patch("services.worker.tasks.scheduler.logger") as mock_logger:
        removed = cleanup_old_report_files_task(days=7)

    assert removed == 0
    assert mock_logger.exception.called


@pytest.mark.integration
def test_cleanup_old_report_files_no_directory(monkeypatch):
    fake_dir = Path("/tmp/non_existing_reports_dir_1234")
    monkeypatch.setattr("core.report.xls_generator.REPORTS_DIR", fake_dir)

    result = cleanup_old_report_files_task(days=7)
    assert result == 0


@pytest.mark.integration
def test_vacuum_analyze_task_executes_sql():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn

    with patch("services.worker.tasks.scheduler.pg_conn", return_value=mock_conn):
        vacuum_analyze_task()

    mock_cursor.execute.assert_called_once_with(
        "VACUUM (VERBOSE, ANALYZE) asset_prices;"
    )
    mock_conn.__enter__.return_value.commit.assert_called_once()


@pytest.mark.integration
def test_cluster_asset_prices_task_executes_sql():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn

    with patch("services.worker.tasks.scheduler.pg_conn", return_value=mock_conn):
        cluster_asset_prices_task()

    mock_cursor.execute.assert_called_once_with(
        "CLUSTER asset_prices USING ix_asset_ticker_date;"
    )
    mock_conn.__enter__.return_value.commit.assert_called_once()
