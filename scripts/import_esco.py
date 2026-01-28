#!/usr/bin/env python3
"""
Standalone script to import ESCO data from CSV ZIP files into SQLite database.

Usage:
    python scripts/import_esco.py --zip_path data/esco_classification_en.zip --db_path data/esco.db --language en
"""

import sys
import os
import csv
import zipfile
import sqlite3
import argparse
import logging
from pathlib import Path
from datetime import datetime
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_database(db_path: str):
    """Create ESCO database with schema."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'create_esco_db.sql')
    
    if not os.path.exists(sql_file):
        logger.error(f"SQL schema file not found: {sql_file}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    with open(sql_file, 'r') as f:
        conn.executescript(f.read())
    conn.close()
    logger.info(f"Database created: {db_path}")


def import_occupations(cursor: sqlite3.Cursor, csv_file: Path, language: str) -> dict:
    """Import occupations from CSV."""
    stats = {'created': 0, 'updated': 0}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = 0
        
        for row in reader:
            total += 1
            if total % 5000 == 0:
                logger.info(f"  Processing occupation {total}...")
            
            uri = row.get('conceptUri', '').strip()
            code = row.get('code', '').strip() or row.get('iscoGroup', '').strip()
            title = row.get('preferredLabel', '').strip()
            description = row.get('description', '').strip() or None
            
            if not uri or not title:
                continue
            
            # Limit description length
            if description and len(description) > 10000:
                description = description[:10000]
            
            # Parse modified_date
            modified_date_str = row.get('modifiedDate', '').strip()
            modified_date = None
            if modified_date_str:
                try:
                    dt = datetime.fromisoformat(modified_date_str.replace('Z', '+00:00'))
                    modified_date = dt.isoformat()  # Convert to string for SQLite
                except:
                    pass
            
            # Check if exists
            cursor.execute("SELECT id FROM esco_occupation WHERE uri = ? AND language = ?", (uri, language))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE esco_occupation 
                    SET code = ?, title = ?, description = ?, modified_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (code, title, description, modified_date, existing[0]))
                stats['updated'] += 1
            else:
                cursor.execute("""
                    INSERT INTO esco_occupation 
                    (uri, language, code, title, description, status, isco_group, modified_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    uri, language, code, title, description,
                    row.get('status', '').strip() or None,
                    row.get('iscoGroup', '').strip() or None,
                    modified_date
                ))
                stats['created'] += 1
    
    return stats


def import_skills(cursor: sqlite3.Cursor, csv_file: Path, language: str) -> dict:
    """Import skills from CSV."""
    stats = {'created': 0, 'updated': 0}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = 0
        
        for row in reader:
            total += 1
            if total % 10000 == 0:
                logger.info(f"  Processing skill {total}...")
            
            uri = row.get('conceptUri', '').strip()
            title = row.get('preferredLabel', '').strip()
            description = row.get('description', '').strip() or None
            
            if not uri or not title:
                continue
            
            # Limit description length
            if description and len(description) > 10000:
                description = description[:10000]
            
            # Parse modified_date
            modified_date_str = row.get('modifiedDate', '').strip()
            modified_date = None
            if modified_date_str:
                try:
                    dt = datetime.fromisoformat(modified_date_str.replace('Z', '+00:00'))
                    modified_date = dt.isoformat()  # Convert to string for SQLite
                except:
                    pass
            
            # Check if exists
            cursor.execute("SELECT id FROM esco_skill WHERE uri = ? AND language = ?", (uri, language))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE esco_skill 
                    SET title = ?, description = ?, skill_type = ?, reuse_level = ?, modified_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    title, description,
                    row.get('skillType', '').strip() or None,
                    row.get('reuseLevel', '').strip() or None,
                    modified_date, existing[0]
                ))
                stats['updated'] += 1
            else:
                cursor.execute("""
                    INSERT INTO esco_skill 
                    (uri, language, title, description, skill_type, reuse_level, status, modified_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    uri, language, title, description,
                    row.get('skillType', '').strip() or None,
                    row.get('reuseLevel', '').strip() or None,
                    row.get('status', '').strip() or None,
                    modified_date
                ))
                stats['created'] += 1
    
    return stats


def import_relations(cursor: sqlite3.Cursor, csv_file: Path, language: str) -> int:
    """Import occupation-skill relations from CSV."""
    created_count = 0
    
    # Build URI to ID maps
    cursor.execute("SELECT id, uri FROM esco_occupation WHERE language = ?", (language,))
    occupation_map = {uri: id for id, uri in cursor.fetchall()}
    
    cursor.execute("SELECT id, uri FROM esco_skill WHERE language = ?", (language,))
    skill_map = {uri: id for id, uri in cursor.fetchall()}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = 0
        batch = []
        
        for row in reader:
            total += 1
            if total % 10000 == 0:
                logger.info(f"  Processing relation {total}...")
            
            occupation_uri = row.get('occupationUri', '').strip()
            skill_uri = row.get('skillUri', '').strip()
            relation_type = row.get('relationType', '').strip().lower()
            is_essential = (relation_type == 'essential')
            
            if not occupation_uri or not skill_uri:
                continue
            
            occupation_id = occupation_map.get(occupation_uri)
            skill_id = skill_map.get(skill_uri)
            
            if not occupation_id or not skill_id:
                continue
            
            batch.append((occupation_id, skill_id, is_essential))
            
            # Insert in batches
            if len(batch) >= 1000:
                cursor.executemany("""
                    INSERT OR IGNORE INTO esco_occupation_skill (occupation_id, skill_id, is_essential)
                    VALUES (?, ?, ?)
                """, batch)
                created_count += cursor.rowcount
                batch = []
        
        # Insert remaining
        if batch:
            cursor.executemany("""
                INSERT OR IGNORE INTO esco_occupation_skill (occupation_id, skill_id, is_essential)
                VALUES (?, ?, ?)
            """, batch)
            created_count += cursor.rowcount
    
    return created_count


def main():
    parser = argparse.ArgumentParser(
        description='Import ESCO data from CSV ZIP file to SQLite database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Create database and import English data
    python scripts/import_esco.py --zip_path data/esco_classification_en.zip --db_path data/esco.db --language en
    
    # Import additional language
    python scripts/import_esco.py --zip_path data/esco_classification_it.zip --db_path data/esco.db --language it
        """
    )
    
    parser.add_argument('--zip_path', type=str, required=True,
                       help='Path to ESCO CSV ZIP file')
    parser.add_argument('--db_path', type=str, required=True,
                       help='Path to SQLite database file (will be created if not exists)')
    parser.add_argument('--language', type=str, default='en',
                       choices=['en', 'de', 'es', 'fr', 'it'],
                       help='Language code (default: en)')
    parser.add_argument('--skip-skills', action='store_true',
                       help='Skip importing skills')
    parser.add_argument('--skip-relations', action='store_true',
                       help='Skip importing occupation-skill relations')
    
    args = parser.parse_args()
    
    # Check ZIP file
    if not os.path.exists(args.zip_path):
        logger.error(f"ZIP file not found: {args.zip_path}")
        sys.exit(1)
    
    # Create database if not exists
    if not os.path.exists(args.db_path):
        logger.info(f"Creating database: {args.db_path}")
        create_database(args.db_path)
    else:
        logger.info(f"Using existing database: {args.db_path}")
    
    # Connect to database
    conn = sqlite3.connect(args.db_path)
    cursor = conn.cursor()
    
    try:
        # Extract ZIP to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            logger.info(f"Extracting {args.zip_path}...")
            with zipfile.ZipFile(args.zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            
            stats = {
                'occupations_created': 0,
                'occupations_updated': 0,
                'skills_created': 0,
                'skills_updated': 0,
                'relations_created': 0,
            }
            
            # Import occupations
            logger.info(f"Importing occupations for language {args.language}...")
            occupations_file = temp_path / f'occupations_{args.language}.csv'
            if occupations_file.exists():
                occ_stats = import_occupations(cursor, occupations_file, args.language)
                stats['occupations_created'] = occ_stats['created']
                stats['occupations_updated'] = occ_stats['updated']
                conn.commit()
                logger.info(f"  {occ_stats['created']} created, {occ_stats['updated']} updated")
            else:
                logger.warning(f"  WARNING: File not found: {occupations_file.name}")
            
            # Import skills
            if not args.skip_skills:
                logger.info(f"Importing skills for language {args.language}...")
                skills_file = temp_path / f'skills_{args.language}.csv'
                if skills_file.exists():
                    skill_stats = import_skills(cursor, skills_file, args.language)
                    stats['skills_created'] = skill_stats['created']
                    stats['skills_updated'] = skill_stats['updated']
                    conn.commit()
                    logger.info(f"  {skill_stats['created']} created, {skill_stats['updated']} updated")
                else:
                    logger.warning(f"  WARNING: File not found: {skills_file.name}")
            
            # Import relations
            if not args.skip_relations and not args.skip_skills:
                logger.info(f"Importing occupation-skill relations for language {args.language}...")
                relations_file = temp_path / f'occupationSkillRelations_{args.language}.csv'
                if relations_file.exists():
                    relations_count = import_relations(cursor, relations_file, args.language)
                    stats['relations_created'] = relations_count
                    conn.commit()
                    logger.info(f"  {relations_count} relations created")
                else:
                    logger.warning(f"  WARNING: File not found: {relations_file.name}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("IMPORT COMPLETE - Summary")
        logger.info("="*60)
        logger.info(f"Occupations: {stats['occupations_created']} created, {stats['occupations_updated']} updated")
        if not args.skip_skills:
            logger.info(f"Skills: {stats['skills_created']} created, {stats['skills_updated']} updated")
        if not args.skip_relations:
            logger.info(f"Relations: {stats['relations_created']} created")
        logger.info("="*60)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error during import: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
