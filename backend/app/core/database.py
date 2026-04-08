import aiosqlite
from pathlib import Path
from datetime import datetime
from ..core.config import settings

DB_VERSION = 1


async def init_db():
    """Initialize database on first startup. Auto-creates all tables and indexes."""
    db_path = settings.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(str(db_path)) as db:
        # User profiles table
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                common_issue_types TEXT DEFAULT '[]',
                triggered_emotional_axes TEXT DEFAULT '[]',
                preferred_output_style TEXT DEFAULT 'dramatic',
                resonant_seats TEXT DEFAULT '[]',
                major_cases TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Seat memories table
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS seat_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                seat_id TEXT NOT NULL,
                recent_suppression_count INTEGER DEFAULT 0,
                consecutive_minority_rounds INTEGER DEFAULT 0,
                common_oppose_issues TEXT DEFAULT '[]',
                common_allies TEXT DEFAULT '[]',
                user_interaction_impression TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, seat_id)
            )
        """
        )

        # Council archive table
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                proposal_title TEXT NOT NULL,
                conclusion TEXT,
                minority_opinion TEXT,
                bell_damage_records TEXT DEFAULT '[]',
                triggered_reconsider BOOLEAN DEFAULT FALSE,
                triggered_fracture BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                proposal_embedding BLOB,
                conclusion_embedding BLOB
            )
        """
        )

        # Bell damage records table
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bell_damage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                seat_id TEXT NOT NULL,
                damage_amount INTEGER DEFAULT 0,
                fracture_triggered BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(case_id)
            )
        """
        )

        # Create indexes
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_seat_memory_user_seat
            ON seat_memories(user_id, seat_id)
        """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cases_user_created
            ON cases(user_id, created_at DESC)
        """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cases_conclusion_type
            ON cases(triggered_reconsider, triggered_fracture)
        """
        )

        # Version table
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY
            )
        """
        )
        await db.execute(
            "INSERT OR IGNORE INTO db_version (version) VALUES (?)", (DB_VERSION,)
        )

        await db.commit()

    print(f"[OK] Database initialized: {db_path}")


async def backup_db():
    """Backup database to backups/ directory."""
    import shutil

    db_path = settings.DB_PATH
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    if db_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"council_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        print(f"[BACKUP] Database backed up: {backup_path}")


async def get_db():
    """Get database connection context manager."""
    db_path = settings.DB_PATH
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        yield db
