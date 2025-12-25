"""
RetroAuto v2 - Run History & Orchestration

SQLite-based run history tracking for automation executions.

Phase: Quick wins (OCR + Run History)
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from infra import get_logger

logger = get_logger("RunHistory")


@dataclass
class RunRecord:
    """Record of a single automation run."""

    run_id: str
    script_path: str
    script_name: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str = "running"  # running, success, failed, stopped
    steps_completed: int = 0
    total_steps: int = 0
    error_message: str | None = None
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "script_path": self.script_path,
            "script_name": self.script_name,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "steps_completed": self.steps_completed,
            "total_steps": self.total_steps,
            "error_message": self.error_message,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }


class RunHistory:
    """
    SQLite-based run history manager.

    Features:
    - Track all automation runs
    - Store start/end times, status, errors
    - Link to artifacts (screenshots, logs)
    - Query history with filters

    Usage:
        history = RunHistory("runs.db")
        run_id = history.start_run("script.yaml", "My Script")
        history.update_step(run_id, 5, 10)
        history.end_run(run_id, "success")
        
        runs = history.get_runs(limit=10)
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        """
        Initialize run history.

        Args:
            db_path: Path to SQLite database (None = in-memory)
        """
        if db_path is None:
            self._db_path = ":memory:"
        else:
            self._db_path = str(db_path)
            # Ensure directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                script_path TEXT NOT NULL,
                script_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                status TEXT DEFAULT 'running',
                steps_completed INTEGER DEFAULT 0,
                total_steps INTEGER DEFAULT 0,
                error_message TEXT,
                artifacts TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}'
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_started
            ON runs (started_at DESC)
        """)
        conn.commit()
        logger.info("Run history database initialized: %s", self._db_path)

    def start_run(
        self,
        script_path: str,
        script_name: str,
        total_steps: int = 0,
        metadata: dict | None = None,
    ) -> str:
        """
        Start tracking a new run.

        Returns:
            run_id: Unique identifier for this run
        """
        run_id = str(uuid.uuid4())[:8]
        started_at = datetime.now().isoformat()

        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO runs (run_id, script_path, script_name, started_at, 
                              total_steps, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                script_path,
                script_name,
                started_at,
                total_steps,
                json.dumps(metadata or {}),
            ),
        )
        conn.commit()

        logger.info("Run started: %s (%s)", run_id, script_name)
        return run_id

    def update_step(
        self,
        run_id: str,
        steps_completed: int,
        total_steps: int | None = None,
    ) -> None:
        """Update progress of a run."""
        conn = self._get_conn()
        if total_steps is not None:
            conn.execute(
                "UPDATE runs SET steps_completed = ?, total_steps = ? WHERE run_id = ?",
                (steps_completed, total_steps, run_id),
            )
        else:
            conn.execute(
                "UPDATE runs SET steps_completed = ? WHERE run_id = ?",
                (steps_completed, run_id),
            )
        conn.commit()

    def add_artifact(self, run_id: str, artifact_path: str) -> None:
        """Add an artifact (screenshot, log) to a run."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT artifacts FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        
        if row:
            artifacts = json.loads(row["artifacts"])
            artifacts.append(artifact_path)
            conn.execute(
                "UPDATE runs SET artifacts = ? WHERE run_id = ?",
                (json.dumps(artifacts), run_id),
            )
            conn.commit()

    def end_run(
        self,
        run_id: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """
        End a run.

        Args:
            run_id: Run to end
            status: Final status (success, failed, stopped)
            error_message: Optional error message if failed
        """
        ended_at = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            """
            UPDATE runs SET ended_at = ?, status = ?, error_message = ?
            WHERE run_id = ?
            """,
            (ended_at, status, error_message, run_id),
        )
        conn.commit()

        logger.info("Run ended: %s (status=%s)", run_id, status)

    def get_run(self, run_id: str) -> RunRecord | None:
        """Get a specific run by ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        
        if row:
            return self._row_to_record(row)
        return None

    def get_runs(
        self,
        limit: int = 50,
        status: str | None = None,
        script_name: str | None = None,
    ) -> list[RunRecord]:
        """
        Get run history.

        Args:
            limit: Maximum number of runs to return
            status: Filter by status
            script_name: Filter by script name

        Returns:
            List of RunRecords, newest first
        """
        conn = self._get_conn()
        query = "SELECT * FROM runs"
        params: list[Any] = []
        conditions = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if script_name:
            conditions.append("script_name LIKE ?")
            params.append(f"%{script_name}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_stats(self) -> dict[str, Any]:
        """Get run statistics."""
        conn = self._get_conn()
        
        total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        success = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE status = 'success'"
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE status = 'failed'"
        ).fetchone()[0]
        
        return {
            "total_runs": total,
            "successful": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
        }

    def clear_history(self, before_days: int | None = None) -> int:
        """
        Clear run history.

        Args:
            before_days: Only clear runs older than N days (None = all)

        Returns:
            Number of runs deleted
        """
        conn = self._get_conn()
        
        if before_days is not None:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=before_days)).isoformat()
            result = conn.execute(
                "DELETE FROM runs WHERE started_at < ?", (cutoff,)
            )
        else:
            result = conn.execute("DELETE FROM runs")
        
        conn.commit()
        return result.rowcount

    def _row_to_record(self, row: sqlite3.Row) -> RunRecord:
        """Convert database row to RunRecord."""
        return RunRecord(
            run_id=row["run_id"],
            script_path=row["script_path"],
            script_name=row["script_name"],
            started_at=datetime.fromisoformat(row["started_at"]),
            ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
            status=row["status"],
            steps_completed=row["steps_completed"],
            total_steps=row["total_steps"],
            error_message=row["error_message"],
            artifacts=json.loads(row["artifacts"]),
            metadata=json.loads(row["metadata"]),
        )

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# Singleton for global access
_default_history: RunHistory | None = None


def get_run_history(db_path: Path | str | None = None) -> RunHistory:
    """Get the default run history instance."""
    global _default_history
    if _default_history is None:
        if db_path is None:
            db_path = Path.home() / ".retroauto" / "runs.db"
        _default_history = RunHistory(db_path)
    return _default_history
