#!/usr/bin/env python3
"""CLI: создание резервной копии DBCS (по расписанию или принудительно).

Примеры:
  PYTHONPATH=. .venv/bin/python additional_scripts/run_backup.py --if-due
  PYTHONPATH=. .venv/bin/python additional_scripts/run_backup.py --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="DBCS backup runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--if-due",
        action="store_true",
        help="Создать копию только если сработало расписание",
    )
    group.add_argument(
        "--force",
        action="store_true",
        help="Создать копию принудительно",
    )
    args = parser.parse_args()

    from app.db.session import SessionLocal
    from app.services import backup_service
    from app.services.backup_service import BackupError

    db = SessionLocal()
    try:
        if args.force:
            info = backup_service.create_backup(db)
            print(f"OK force: {info.filename} ({info.size_bytes} bytes)")
            return 0

        info = backup_service.run_scheduled_if_due(db)
        if info is None:
            print("SKIP: backup not due")
            return 0
        print(f"OK scheduled: {info.filename} ({info.size_bytes} bytes)")
        return 0
    except BackupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
