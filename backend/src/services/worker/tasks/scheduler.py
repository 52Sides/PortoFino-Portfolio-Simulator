import logging
from datetime import datetime, timedelta, timezone

import psycopg2
from celery import shared_task
from core.config import settings
from core.report.xls_generator import REPORTS_DIR

logger = logging.getLogger(__name__)

SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")


def pg_conn():
    return psycopg2.connect(SYNC_DB_URL)


@shared_task(name="vacuum_analyze_task")
def vacuum_analyze_task():
    """VACUUM ANALYZE asset_prices."""
    try:
        with pg_conn() as conn:
            with conn.cursor() as cur:
                logger.info("VACUUM (VERBOSE, ANALYZE) asset_prices...")
                cur.execute("VACUUM (VERBOSE, ANALYZE) asset_prices;")
            conn.commit()
        logger.info("VACUUM completed")
    except Exception as e:
        logger.exception(f"VACUUM failed: {e}")


@shared_task(name="cluster_asset_prices_task")
def cluster_asset_prices_task():
    """CLUSTER asset_prices BY index."""
    try:
        with pg_conn() as conn:
            with conn.cursor() as cur:
                logger.info("CLUSTER asset_prices USING ix_asset_ticker_date...")
                cur.execute("CLUSTER asset_prices USING ix_asset_ticker_date;")
            conn.commit()
        logger.info("CLUSTER completed")
    except Exception as e:
        logger.exception(f"CLUSTER failed: {e}")


@shared_task(name="cleanup_old_report_files_task")
def cleanup_old_report_files_task(days: int = 7) -> int:
    """
    Delete report files named report_*.xls or report_*.xlsx older than [days].
    Returns number of deleted files.
    """
    deleted = 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    if not REPORTS_DIR.exists():
        logger.info(f"[cleanup] Reports dir does not exist: {REPORTS_DIR}")
        return 0

    patterns = ("report_*.xlsx", "report_*.xls")
    for pattern in patterns:
        for p in REPORTS_DIR.glob(pattern):
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if mtime < cutoff:
                    logger.info(f"[cleanup] Removing old report: {p} (mtime={mtime.isoformat()})")
                    try:
                        p.unlink()
                        deleted += 1
                    except Exception as e:
                        logger.exception(f"[cleanup] Failed to remove {p}: {e}")
            except Exception as e:
                logger.exception(f"[cleanup] Error checking file {p}: {e}")

    logger.info(f"[cleanup] Completed. Files removed: {deleted}")
    return deleted
