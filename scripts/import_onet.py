#!/usr/bin/env python3
"""
Standalone script to import ONET data from text ZIP file into SQLite database.

Imports: Occupation Data, Task Statements + Task Ratings (IM), Technology Skills.
Output: onet_occupation, onet_task, onet_occupation_task, onet_technology_skill, onet_occupation_technology_skill.

Usage:
    python scripts/import_onet.py --zip_path data/db_30_1_text.zip --db_path data/onet.db
"""

import sys
import os
import csv
import zipfile
import sqlite3
import argparse
import logging
from pathlib import Path
from decimal import Decimal, InvalidOperation
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_database(db_path: str):
    """Create ONET database with schema."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'create_onet_db.sql')

    if not os.path.exists(sql_file):
        logger.error(f"SQL schema file not found: {sql_file}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    with open(sql_file, 'r') as f:
        conn.executescript(f.read())
    conn.close()
    logger.info(f"Database created: {db_path}")


def import_occupations(cursor: sqlite3.Cursor, txt_file: Path) -> dict:
    """Import occupations from Occupation Data.txt"""
    stats = {'created': 0, 'updated': 0}

    with open(txt_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        total = 0

        for row in reader:
            total += 1
            if total % 1000 == 0:
                logger.info(f"  Processing occupation {total}...")

            code = row.get('O*NET-SOC Code', '').strip()
            title = row.get('Title', '').strip()
            description = row.get('Description', '').strip() or None

            if not code or not title:
                continue

            cursor.execute("SELECT id FROM onet_occupation WHERE code = ?", (code,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE onet_occupation
                    SET title = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (title, description, existing[0]))
                stats['updated'] += 1
            else:
                cursor.execute("""
                    INSERT INTO onet_occupation (code, title, description)
                    VALUES (?, ?, ?)
                """, (code, title, description))
                stats['created'] += 1

    return stats


def import_tasks(cursor: sqlite3.Cursor, txt_file: Path) -> dict:
    """Import unique tasks from Task Statements.txt (task_id, task_text)."""
    stats = {'created': 0, 'updated': 0}
    seen_task_ids = set()

    with open(txt_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        total = 0

        for row in reader:
            total += 1
            if total % 5000 == 0:
                logger.info(f"  Processing task statement {total}...")

            task_id = row.get('Task ID', '').strip()
            task_text = row.get('Task', '').strip() or None

            if not task_id:
                continue
            if task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)

            cursor.execute("SELECT id FROM onet_task WHERE task_id = ?", (task_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE onet_task
                    SET task_text = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (task_text, existing[0]))
                stats['updated'] += 1
            else:
                cursor.execute("""
                    INSERT INTO onet_task (task_id, task_text)
                    VALUES (?, ?)
                """, (task_id, task_text))
                stats['created'] += 1

    return stats


def import_occupation_task_ratings(cursor: sqlite3.Cursor, txt_file: Path) -> int:
    """Import occupation-task ratings from Task Ratings.txt (IM scale only)."""
    created_count = 0

    cursor.execute("SELECT id, code FROM onet_occupation")
    occupation_map = {code: id for id, code in cursor.fetchall()}

    cursor.execute("SELECT id, task_id FROM onet_task")
    task_map = {task_id: id for id, task_id in cursor.fetchall()}

    with open(txt_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        total = 0
        batch = []

        for row in reader:
            total += 1
            if total % 20000 == 0:
                logger.info(f"  Processing task rating {total}...")

            code = row.get('O*NET-SOC Code', '').strip()
            task_id_str = row.get('Task ID', '').strip()
            scale_id = row.get('Scale ID', '').strip()
            data_value_str = row.get('Data Value', '').strip()

            if scale_id != 'IM' or not code or not task_id_str or not data_value_str:
                continue

            occupation_id = occupation_map.get(code)
            task_pk = task_map.get(task_id_str)

            if not occupation_id or not task_pk:
                continue

            try:
                data_value = float(data_value_str)
            except (ValueError, InvalidOperation):
                continue

            batch.append((occupation_id, task_pk, scale_id, data_value))

            if len(batch) >= 1000:
                cursor.executemany("""
                    INSERT OR IGNORE INTO onet_occupation_task
                    (occupation_id, task_id, scale_id, data_value)
                    VALUES (?, ?, ?, ?)
                """, batch)
                created_count += len(batch)
                batch = []

        if batch:
            cursor.executemany("""
                INSERT OR IGNORE INTO onet_occupation_task
                (occupation_id, task_id, scale_id, data_value)
                VALUES (?, ?, ?, ?)
            """, batch)
            created_count += len(batch)

    return created_count


def import_technology_skills(cursor: sqlite3.Cursor, txt_file: Path) -> dict:
    """Import unique technology skills from Technology Skills.txt (example, commodity_code, commodity_title)."""
    stats = {'created': 0, 'updated': 0}
    seen_examples = set()

    with open(txt_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        total = 0

        for row in reader:
            total += 1
            if total % 5000 == 0:
                logger.info(f"  Processing technology skill {total}...")

            example = row.get('Example', '').strip()
            commodity_code = row.get('Commodity Code', '').strip() or None
            commodity_title = row.get('Commodity Title', '').strip() or None

            if not example:
                continue
            if example in seen_examples:
                continue
            seen_examples.add(example)

            cursor.execute("SELECT id FROM onet_technology_skill WHERE example = ?", (example,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE onet_technology_skill
                    SET commodity_code = ?, commodity_title = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (commodity_code, commodity_title, existing[0]))
                stats['updated'] += 1
            else:
                cursor.execute("""
                    INSERT INTO onet_technology_skill (example, commodity_code, commodity_title)
                    VALUES (?, ?, ?)
                """, (example, commodity_code, commodity_title))
                stats['created'] += 1

    return stats


def import_occupation_technology_skills(cursor: sqlite3.Cursor, txt_file: Path) -> int:
    """Import occupation-technology_skill relations with derived weight (1.0 if Hot or In Demand, else 0.5)."""
    created_count = 0

    cursor.execute("SELECT id, code FROM onet_occupation")
    occupation_map = {code: id for id, code in cursor.fetchall()}

    cursor.execute("SELECT id, example FROM onet_technology_skill")
    tech_skill_map = {example: id for id, example in cursor.fetchall()}

    with open(txt_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        total = 0
        batch = []

        for row in reader:
            total += 1
            if total % 10000 == 0:
                logger.info(f"  Processing occupation-tech skill {total}...")

            code = row.get('O*NET-SOC Code', '').strip()
            example = row.get('Example', '').strip()
            hot = (row.get('Hot Technology', '').strip().upper() == 'Y')
            in_demand = (row.get('In Demand', '').strip().upper() == 'Y')
            weight = 1.0 if (hot or in_demand) else 0.5

            if not code or not example:
                continue

            occupation_id = occupation_map.get(code)
            tech_skill_id = tech_skill_map.get(example)

            if not occupation_id or not tech_skill_id:
                continue

            batch.append((occupation_id, tech_skill_id, weight))

            if len(batch) >= 1000:
                cursor.executemany("""
                    INSERT OR IGNORE INTO onet_occupation_technology_skill
                    (occupation_id, technology_skill_id, weight)
                    VALUES (?, ?, ?)
                """, batch)
                created_count += len(batch)
                batch = []

        if batch:
            cursor.executemany("""
                INSERT OR IGNORE INTO onet_occupation_technology_skill
                (occupation_id, technology_skill_id, weight)
                VALUES (?, ?, ?)
            """, batch)
            created_count += len(batch)

    return created_count


def main():
    parser = argparse.ArgumentParser(
        description='Import ONET data (occupations, tasks, technology skills) from text ZIP to SQLite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Create database and import all data
    python scripts/import_onet.py --zip_path data/db_30_1_text.zip --db_path data/onet.db

    # Recreate database from scratch (drops existing tables and recreates)
    python scripts/import_onet.py --zip_path data/db_30_1_text.zip --db_path data/onet.db --recreate

    # Skip tasks or technology skills (e.g. for faster partial import)
    python scripts/import_onet.py --zip_path data/db_30_1_text.zip --db_path data/onet.db --skip-tasks
        """
    )

    parser.add_argument('--zip_path', type=str, required=True,
                        help='Path to ONET text ZIP file (db_30_1_text.zip)')
    parser.add_argument('--db_path', type=str, required=True,
                        help='Path to SQLite database file (will be created if not exists)')
    parser.add_argument('--recreate', action='store_true',
                        help='Recreate database: delete file if exists and create from schema')
    parser.add_argument('--skip-tasks', action='store_true',
                        help='Skip importing tasks and occupation-task ratings')
    parser.add_argument('--skip-tech-skills', action='store_true',
                        help='Skip importing technology skills and occupation-technology_skill relations')

    args = parser.parse_args()

    if not os.path.exists(args.zip_path):
        logger.error(f"ZIP file not found: {args.zip_path}")
        sys.exit(1)

    if args.recreate and os.path.exists(args.db_path):
        logger.info(f"Removing existing database: {args.db_path}")
        os.remove(args.db_path)

    if not os.path.exists(args.db_path):
        logger.info(f"Creating database: {args.db_path}")
        create_database(args.db_path)
    else:
        logger.info(f"Using existing database: {args.db_path}")

    conn = sqlite3.connect(args.db_path)
    cursor = conn.cursor()

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            logger.info(f"Extracting {args.zip_path}...")
            with zipfile.ZipFile(args.zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)

            db_text_dir = temp_path / 'db_30_1_text'

            if not db_text_dir.exists():
                logger.error("Expected directory db_30_1_text not found in ZIP")
                sys.exit(1)

            stats = {
                'occupations_created': 0,
                'occupations_updated': 0,
                'tasks_created': 0,
                'tasks_updated': 0,
                'occupation_task_ratings': 0,
                'tech_skills_created': 0,
                'tech_skills_updated': 0,
                'occupation_tech_skill_rels': 0,
            }

            # Occupations
            logger.info("Importing occupations...")
            occupations_file = db_text_dir / 'Occupation Data.txt'
            if occupations_file.exists():
                occ_stats = import_occupations(cursor, occupations_file)
                stats['occupations_created'] = occ_stats['created']
                stats['occupations_updated'] = occ_stats['updated']
                conn.commit()
                logger.info(f"  {occ_stats['created']} created, {occ_stats['updated']} updated")
            else:
                logger.warning("  WARNING: Occupation Data.txt not found")

            # Tasks: Task Statements -> onet_task, then Task Ratings (IM) -> onet_occupation_task
            if not args.skip_tasks:
                task_statements = db_text_dir / 'Task Statements.txt'
                task_ratings = db_text_dir / 'Task Ratings.txt'
                if task_statements.exists():
                    logger.info("Importing tasks (Task Statements)...")
                    task_stats = import_tasks(cursor, task_statements)
                    stats['tasks_created'] = task_stats['created']
                    stats['tasks_updated'] = task_stats['updated']
                    conn.commit()
                    logger.info(f"  {task_stats['created']} created, {task_stats['updated']} updated")
                if task_ratings.exists():
                    logger.info("Importing occupation-task ratings (IM scale)...")
                    ratings_count = import_occupation_task_ratings(cursor, task_ratings)
                    stats['occupation_task_ratings'] = ratings_count
                    conn.commit()
                    logger.info(f"  {ratings_count} ratings created")
                if not task_statements.exists() or not task_ratings.exists():
                    logger.warning("  WARNING: Task Statements.txt or Task Ratings.txt not found")

            # Technology skills
            if not args.skip_tech_skills:
                tech_skills_file = db_text_dir / 'Technology Skills.txt'
                if tech_skills_file.exists():
                    logger.info("Importing technology skills...")
                    ts_stats = import_technology_skills(cursor, tech_skills_file)
                    stats['tech_skills_created'] = ts_stats['created']
                    stats['tech_skills_updated'] = ts_stats['updated']
                    conn.commit()
                    logger.info(f"  {ts_stats['created']} created, {ts_stats['updated']} updated")
                    logger.info("Importing occupation-technology_skill relations...")
                    rels_count = import_occupation_technology_skills(cursor, tech_skills_file)
                    stats['occupation_tech_skill_rels'] = rels_count
                    conn.commit()
                    logger.info(f"  {rels_count} relations created")
                else:
                    logger.warning("  WARNING: Technology Skills.txt not found")

        logger.info("\n" + "="*60)
        logger.info("IMPORT COMPLETE - Summary")
        logger.info("="*60)
        logger.info(f"Occupations: {stats['occupations_created']} created, {stats['occupations_updated']} updated")
        if not args.skip_tasks:
            logger.info(f"Tasks: {stats['tasks_created']} created, {stats['tasks_updated']} updated")
            logger.info(f"Occupation-task ratings (IM): {stats['occupation_task_ratings']}")
        if not args.skip_tech_skills:
            logger.info(f"Technology skills: {stats['tech_skills_created']} created, {stats['tech_skills_updated']} updated")
            logger.info(f"Occupation-technology_skill relations: {stats['occupation_tech_skill_rels']}")
        logger.info("="*60)

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during import: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
