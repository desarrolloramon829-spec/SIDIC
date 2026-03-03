"""
Repositorio de proyectos basado en SQLite.

Cada proyecto S.I.D.I.C se guarda como un archivo .sidic (SQLite)
que contiene toda la información de archivos cargados, periodos
seleccionados, filtros aplicados y reportes generados.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
SIDIC_EXTENSION = ".sidic"


@dataclass
class ProjectFile:
    """Referencia a un archivo cargado en el proyecto."""

    path: str
    entity_type: str  # "hechos" | "mencionados" | "aprehendidos" | "jurisdiccion"
    file_format: str  # ".shp" | ".geojson" | etc.
    encoding: Optional[str] = None
    record_count: int = 0
    loaded_at: Optional[datetime] = None


@dataclass
class ProjectPeriod:
    """Período de análisis configurado."""

    name: str
    start_date: date
    end_date: date
    files: List[ProjectFile] = field(default_factory=list)
    color: Optional[str] = None


@dataclass
class ProjectInfo:
    """Metadatos del proyecto."""

    name: str
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: str = ""
    jurisdiccion: str = ""
    dependencia: str = ""
    periods: List[ProjectPeriod] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    field_mapping_overrides: Dict[str, Any] = field(default_factory=dict)


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS project_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS periods (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL,
    color      TEXT
);

CREATE TABLE IF NOT EXISTS project_files (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id    INTEGER REFERENCES periods(id) ON DELETE CASCADE,
    path         TEXT NOT NULL,
    entity_type  TEXT NOT NULL,
    file_format  TEXT,
    encoding     TEXT,
    record_count INTEGER DEFAULT 0,
    loaded_at    TEXT
);

CREATE TABLE IF NOT EXISTS filters (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS field_mappings (
    entity TEXT NOT NULL,
    field  TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (entity, field)
);
"""


class ProjectRepository:
    """
    Implementa el Protocol ProjectRepository con SQLite.

    Ejemplo::

        repo = ProjectRepository()
        repo.save(info, Path("mi_proyecto.sidic"))
        info = repo.load(Path("mi_proyecto.sidic"))
    """

    def save(self, info: ProjectInfo, path: Path) -> None:
        """Guarda proyecto en archivo .sidic (SQLite)."""
        path = Path(path)
        if path.suffix.lower() != SIDIC_EXTENSION:
            path = path.with_suffix(SIDIC_EXTENSION)

        conn = sqlite3.connect(str(path))
        try:
            conn.executescript(_SCHEMA_SQL)
            self._save_meta(conn, info)
            self._save_periods(conn, info.periods)
            self._save_filters(conn, info.filters)
            self._save_field_mappings(conn, info.field_mapping_overrides)
            conn.commit()
            logger.info(f"Proyecto guardado: {path}")
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def load(self, path: Path) -> ProjectInfo:
        """Carga proyecto desde archivo .sidic."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Proyecto no encontrado: {path}")

        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        try:
            meta = self._load_meta(conn)
            periods = self._load_periods(conn)
            filters = self._load_filters(conn)
            mappings = self._load_field_mappings(conn)

            return ProjectInfo(
                name=meta.get("name", path.stem),
                description=meta.get("description", ""),
                created_at=_parse_datetime(meta.get("created_at")),
                updated_at=_parse_datetime(meta.get("updated_at")),
                author=meta.get("author", ""),
                jurisdiccion=meta.get("jurisdiccion", ""),
                dependencia=meta.get("dependencia", ""),
                periods=periods,
                filters=filters,
                field_mapping_overrides=mappings,
            )
        finally:
            conn.close()

    def exists(self, path: Path) -> bool:
        """Verifica si el archivo de proyecto existe."""
        return Path(path).exists()

    # ── persistencia interna ──

    @staticmethod
    def _save_meta(conn: sqlite3.Connection, info: ProjectInfo) -> None:
        now = datetime.now().isoformat()
        meta = {
            "schema_version": str(SCHEMA_VERSION),
            "name": info.name,
            "description": info.description,
            "created_at": info.created_at.isoformat() if info.created_at else now,
            "updated_at": now,
            "author": info.author,
            "jurisdiccion": info.jurisdiccion,
            "dependencia": info.dependencia,
        }
        conn.execute("DELETE FROM project_meta")
        for k, v in meta.items():
            conn.execute(
                "INSERT INTO project_meta (key, value) VALUES (?, ?)",
                (k, v),
            )

    @staticmethod
    def _save_periods(
        conn: sqlite3.Connection, periods: List[ProjectPeriod]
    ) -> None:
        conn.execute("DELETE FROM project_files")
        conn.execute("DELETE FROM periods")
        for p in periods:
            cursor = conn.execute(
                "INSERT INTO periods (name, start_date, end_date, color) "
                "VALUES (?, ?, ?, ?)",
                (p.name, p.start_date.isoformat(), p.end_date.isoformat(), p.color),
            )
            period_id = cursor.lastrowid
            for f in p.files:
                conn.execute(
                    "INSERT INTO project_files "
                    "(period_id, path, entity_type, file_format, encoding, "
                    "record_count, loaded_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        period_id,
                        f.path,
                        f.entity_type,
                        f.file_format,
                        f.encoding,
                        f.record_count,
                        f.loaded_at.isoformat() if f.loaded_at else None,
                    ),
                )

    @staticmethod
    def _save_filters(
        conn: sqlite3.Connection, filters: Dict[str, Any]
    ) -> None:
        conn.execute("DELETE FROM filters")
        for k, v in filters.items():
            conn.execute(
                "INSERT INTO filters (key, value) VALUES (?, ?)",
                (k, json.dumps(v, ensure_ascii=False)),
            )

    @staticmethod
    def _save_field_mappings(
        conn: sqlite3.Connection, mappings: Dict[str, Any]
    ) -> None:
        conn.execute("DELETE FROM field_mappings")
        for entity, fields in mappings.items():
            if isinstance(fields, dict):
                for field_name, source in fields.items():
                    conn.execute(
                        "INSERT INTO field_mappings (entity, field, source) "
                        "VALUES (?, ?, ?)",
                        (entity, field_name, str(source)),
                    )

    @staticmethod
    def _load_meta(conn: sqlite3.Connection) -> Dict[str, str]:
        rows = conn.execute("SELECT key, value FROM project_meta").fetchall()
        return {r["key"]: r["value"] for r in rows}

    @staticmethod
    def _load_periods(conn: sqlite3.Connection) -> List[ProjectPeriod]:
        periods: List[ProjectPeriod] = []
        rows = conn.execute(
            "SELECT id, name, start_date, end_date, color FROM periods"
        ).fetchall()

        for r in rows:
            files_rows = conn.execute(
                "SELECT path, entity_type, file_format, encoding, "
                "record_count, loaded_at FROM project_files "
                "WHERE period_id = ?",
                (r["id"],),
            ).fetchall()

            files = [
                ProjectFile(
                    path=f["path"],
                    entity_type=f["entity_type"],
                    file_format=f["file_format"] or "",
                    encoding=f["encoding"],
                    record_count=f["record_count"] or 0,
                    loaded_at=_parse_datetime(f["loaded_at"]),
                )
                for f in files_rows
            ]

            periods.append(
                ProjectPeriod(
                    name=r["name"],
                    start_date=date.fromisoformat(r["start_date"]),
                    end_date=date.fromisoformat(r["end_date"]),
                    files=files,
                    color=r["color"],
                )
            )

        return periods

    @staticmethod
    def _load_filters(conn: sqlite3.Connection) -> Dict[str, Any]:
        rows = conn.execute("SELECT key, value FROM filters").fetchall()
        result: Dict[str, Any] = {}
        for r in rows:
            try:
                result[r["key"]] = json.loads(r["value"])
            except json.JSONDecodeError:
                result[r["key"]] = r["value"]
        return result

    @staticmethod
    def _load_field_mappings(conn: sqlite3.Connection) -> Dict[str, Any]:
        rows = conn.execute(
            "SELECT entity, field, source FROM field_mappings"
        ).fetchall()
        result: Dict[str, Dict[str, str]] = {}
        for r in rows:
            entity = r["entity"]
            if entity not in result:
                result[entity] = {}
            result[entity][r["field"]] = r["source"]
        return result


class SettingsRepository:
    """
    Repositorio de configuración del usuario.

    Persiste preferencias como último directorio, tema, tamaño de ventana,
    etc. en un archivo SQLite en el directorio de usuario.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            app_dir = Path.home() / ".sidic"
            app_dir.mkdir(exist_ok=True)
            path = app_dir / "settings.db"
        self._path = path
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_schema(self) -> None:
        conn = self._get_conn()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings "
            "(key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS recent_files "
            "(path TEXT PRIMARY KEY, opened_at TEXT)"
        )
        conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        row = self._get_conn().execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return row["value"]

    def set(self, key: str, value: Any) -> None:
        """Establece un valor de configuración."""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(value, ensure_ascii=False)),
        )
        conn.commit()

    def save(self) -> None:
        """Fuerza escritura a disco."""
        if self._conn:
            self._conn.commit()

    def load(self) -> Dict[str, Any]:
        """Carga todas las configuraciones como dict."""
        rows = self._get_conn().execute(
            "SELECT key, value FROM settings"
        ).fetchall()
        result: Dict[str, Any] = {}
        for r in rows:
            try:
                result[r["key"]] = json.loads(r["value"])
            except (json.JSONDecodeError, TypeError):
                result[r["key"]] = r["value"]
        return result

    # ── archivos recientes ──

    def add_recent_file(self, path: str) -> None:
        """Agrega un archivo a la lista de recientes."""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO recent_files (path, opened_at) "
            "VALUES (?, ?)",
            (path, datetime.now().isoformat()),
        )
        conn.commit()

    def get_recent_files(self, limit: int = 10) -> List[str]:
        """Retorna los archivos recientes, más reciente primero."""
        rows = self._get_conn().execute(
            "SELECT path FROM recent_files ORDER BY opened_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [r["path"] for r in rows]

    def clear_recent_files(self) -> None:
        """Limpia la lista de archivos recientes."""
        conn = self._get_conn()
        conn.execute("DELETE FROM recent_files")
        conn.commit()

    def close(self) -> None:
        """Cierra la conexión."""
        if self._conn:
            self._conn.close()
            self._conn = None


# ── helpers ──


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parsea un string ISO a datetime, None si falla."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
