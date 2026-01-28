"""
Data Loader for ESCO and ONET Databases

Loads occupation-skill relations from SQLite databases.
"""

import sqlite3
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def load_esco_data(db_path: str, language: str = 'en') -> Tuple[Dict, Dict, List, Dict, Dict]:
    """
    Loads ESCO data from SQLite database.
    
    Args:
        db_path: Path to ESCO SQLite database file
        language: ESCO language (default: 'en')
    
    Returns:
        Tuple of:
        - occupation_to_idx: dict {uri: idx}
        - skill_to_idx: dict {uri: idx}
        - occupation_skill_rels: list of tuples (occ_uri, skill_uri)
        - idx_to_occupation_uri: dict {idx: uri}
        - idx_to_skill_uri: dict {idx: uri}
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    logger.info(f"Loading ESCO data from {db_path} (language={language})")
    
    # Load occupations
    cursor.execute("""
        SELECT uri, id
        FROM esco_occupation
        WHERE language = ?
        ORDER BY id
    """, (language,))
    
    occupations = cursor.fetchall()
    occupation_to_idx = {row['uri']: idx for idx, row in enumerate(occupations)}
    idx_to_occupation_uri = {idx: row['uri'] for idx, row in enumerate(occupations)}
    
    logger.info(f"Loaded {len(occupations)} occupations")
    
    # Load skills
    cursor.execute("""
        SELECT uri, id
        FROM esco_skill
        WHERE language = ?
        ORDER BY id
    """, (language,))
    
    skills = cursor.fetchall()
    skill_to_idx = {row['uri']: idx for idx, row in enumerate(skills)}
    idx_to_skill_uri = {idx: row['uri'] for idx, row in enumerate(skills)}
    
    logger.info(f"Loaded {len(skills)} skills")
    
    # Load occupation-skill relations
    cursor.execute("""
        SELECT DISTINCT 
            occ.uri as occupation_uri,
            sk.uri as skill_uri
        FROM esco_occupation_skill rel
        INNER JOIN esco_occupation occ ON rel.occupation_id = occ.id
        INNER JOIN esco_skill sk ON rel.skill_id = sk.id
        WHERE occ.language = ? AND sk.language = ?
    """, (language, language))
    
    rels = cursor.fetchall()
    occupation_skill_rels = [(row['occupation_uri'], row['skill_uri']) for row in rels]
    
    logger.info(f"Loaded {len(occupation_skill_rels)} occupation-skill relations")
    
    conn.close()
    
    return occupation_to_idx, skill_to_idx, occupation_skill_rels, idx_to_occupation_uri, idx_to_skill_uri


def load_onet_task_data(db_path: str) -> Tuple[Dict, Dict, List, Dict, Dict]:
    """
    Loads ONET task data (occupation x task with IM importance) from SQLite database.

    Returns the same shape as load_esco_data / load_onet_technology_skill_data for
    compatibility with trainer and recommender: occupation_to_idx, skill_to_idx (by task_id),
    rels (occ_code, task_id, importance), idx_to_occupation_code, idx_to_skill_element_id (task_id).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info(f"Loading ONET task data from {db_path}")

    cursor.execute("""
        SELECT code, id
        FROM onet_occupation
        ORDER BY id
    """)
    occupations = cursor.fetchall()
    occupation_to_idx = {row['code']: idx for idx, row in enumerate(occupations)}
    idx_to_occupation_code = {idx: row['code'] for idx, row in enumerate(occupations)}
    logger.info(f"Loaded {len(occupations)} occupations")

    cursor.execute("""
        SELECT task_id, id
        FROM onet_task
        ORDER BY id
    """)
    tasks = cursor.fetchall()
    skill_to_idx = {row['task_id']: idx for idx, row in enumerate(tasks)}
    idx_to_skill_element_id = {idx: row['task_id'] for idx, row in enumerate(tasks)}
    logger.info(f"Loaded {len(tasks)} tasks")

    cursor.execute("""
        SELECT occ.code AS occupation_code, t.task_id, rel.data_value AS importance
        FROM onet_occupation_task rel
        INNER JOIN onet_occupation occ ON rel.occupation_id = occ.id
        INNER JOIN onet_task t ON rel.task_id = t.id
        WHERE rel.scale_id = 'IM'
    """)
    rels = cursor.fetchall()
    occupation_skill_rels = [
        (row['occupation_code'], row['task_id'], float(row['importance']))
        for row in rels
    ]
    logger.info(f"Loaded {len(occupation_skill_rels)} occupation-task relations (IM importance)")
    conn.close()

    return occupation_to_idx, skill_to_idx, occupation_skill_rels, idx_to_occupation_code, idx_to_skill_element_id


def load_onet_technology_skill_data(db_path: str) -> Tuple[Dict, Dict, List, Dict, Dict]:
    """
    Loads ONET technology skill data (occupation x example with derived weight) from SQLite.

    Returns shape compatible with trainer/recommender: occupation_to_idx, skill_to_idx (by example),
    rels (occ_code, example, weight), idx_to_occupation_code, idx_to_skill_uri (example name).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info(f"Loading ONET technology skill data from {db_path}")

    cursor.execute("""
        SELECT code, id
        FROM onet_occupation
        ORDER BY id
    """)
    occupations = cursor.fetchall()
    occupation_to_idx = {row['code']: idx for idx, row in enumerate(occupations)}
    idx_to_occupation_code = {idx: row['code'] for idx, row in enumerate(occupations)}
    logger.info(f"Loaded {len(occupations)} occupations")

    cursor.execute("""
        SELECT example, id
        FROM onet_technology_skill
        ORDER BY id
    """)
    tech_skills = cursor.fetchall()
    skill_to_idx = {row['example']: idx for idx, row in enumerate(tech_skills)}
    idx_to_skill_uri = {idx: row['example'] for idx, row in enumerate(tech_skills)}
    logger.info(f"Loaded {len(tech_skills)} technology skills")

    cursor.execute("""
        SELECT occ.code AS occupation_code, ts.example, rel.weight
        FROM onet_occupation_technology_skill rel
        INNER JOIN onet_occupation occ ON rel.occupation_id = occ.id
        INNER JOIN onet_technology_skill ts ON rel.technology_skill_id = ts.id
    """)
    rels = cursor.fetchall()
    occupation_skill_rels = [
        (row['occupation_code'], row['example'], float(row['weight']))
        for row in rels
    ]
    logger.info(f"Loaded {len(occupation_skill_rels)} occupation-technology_skill relations")
    conn.close()

    return occupation_to_idx, skill_to_idx, occupation_skill_rels, idx_to_occupation_code, idx_to_skill_uri
