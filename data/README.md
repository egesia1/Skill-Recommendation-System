# Data Directory

This directory contains the source data files and generated databases for the Skill Recommendation System.

## 📦 Source Files

### ESCO Data
- `esco_classification_en.zip` - ESCO classification CSV files for English
  - Contains: occupations, skills, and occupation-skill relations
  - Source: [ESCO Portal](https://ec.europa.eu/esco/portal)
  - Size: ~10 MB

### ONET Data
- `db_30_1_text.zip` - ONET 30.1 text database
  - Contains: occupations, skills, and ratings
  - Source: [ONET Resource Center](https://www.onetcenter.org/database.html)
  - Size: ~13 MB
  - **Note:** O*NET "Skills" are only 35 elements; the real counterpart of ESCO's thousands of skills are **Tasks** (~18k) and **Technology Skills** (~8.7k). See [ONET_OCCUPATION_TABLES.md](ONET_OCCUPATION_TABLES.md) for all occupation-linked tables.

## Generated Databases

### ESCO Database
- `esco.db` - SQLite database with ESCO data
  - Size: ~22 MB
  - Contains:
    - 3,039 occupations (English)
    - 13,939 skills (English)
    - 126,051 occupation-skill relations

### ONET Database
- `onet.db` - SQLite database with ONET data
  - Contains:
    - ~1,016 occupations
    - ~18,000 tasks (from Task Statements)
    - ~17,000+ occupation-task ratings (IM scale from Task Ratings)
    - ~8,700 technology skills (from Technology Skills.txt)
    - ~32,000 occupation-technology_skill relations (derived weight)

## Generating Databases

### First Time Setup

If the databases don't exist, run the import scripts:

**ESCO:**
```bash
cd /path/to/skill_recommendation
python scripts/import_esco.py \
    --zip_path data/esco_classification_en.zip \
    --db_path data/esco.db \
    --language en
```

**ONET:**
```bash
cd /path/to/skill_recommendation
python scripts/import_onet.py \
    --zip_path data/db_30_1_text.zip \
    --db_path data/onet.db \
    --recreate
```
Use `--recreate` to replace an existing database with the new schema (tasks + technology skills).

### Expected Output

**ESCO Import:**
- Creates `data/esco.db` if it doesn't exist
- Imports ~3,000 occupations
- Imports ~14,000 skills
- Imports ~126,000 relations
- Takes ~2-3 seconds

**ONET Import:**
- Creates `data/onet.db` (or replaces with `--recreate`)
- Imports ~1,000 occupations
- Imports ~18,000 tasks (Task Statements) and occupation-task ratings (Task Ratings, IM scale)
- Imports ~8,700 technology skills and occupation-technology_skill relations (derived weight)
- Takes ~1-2 minutes

## 🔄 Regenerating Databases

To regenerate the databases (useful if schema changes or data corruption):

### Option 1: Delete and Recreate

```bash
# Remove existing databases
rm data/esco.db data/onet.db

# Reimport ESCO
python scripts/import_esco.py \
    --zip_path data/esco_classification_en.zip \
    --db_path data/esco.db \
    --language en

# Reimport ONET (use --recreate to apply new schema)
python scripts/import_onet.py \
    --zip_path data/db_30_1_text.zip \
    --db_path data/onet.db \
    --recreate
```

### Option 2: Overwrite Existing

The import scripts automatically handle existing databases:
- **Update** existing records (based on URI/code)
- **Insert** new records
- **Skip** duplicates (based on unique constraints)

Simply run the import scripts again - they will update the existing databases.

## Verification

Check that databases were created correctly:

```bash
# ESCO
sqlite3 data/esco.db "SELECT COUNT(*) FROM esco_occupation WHERE language='en';"
# Expected: 3039

sqlite3 data/esco.db "SELECT COUNT(*) FROM esco_skill WHERE language='en';"
# Expected: 13939

sqlite3 data/esco.db "SELECT COUNT(*) FROM esco_occupation_skill;"
# Expected: 126051

# ONET
sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_occupation;"
# Expected: ~1016

sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_task;"
# Expected: ~18000

sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_occupation_task WHERE scale_id='IM';"
# Expected: ~17000+

sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_technology_skill;"
# Expected: ~8700

sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_occupation_technology_skill;"
# Expected: ~32000
```

## Notes

- **File Sizes**: ZIP files are ~10-15 MB each, databases are ~4-22 MB each
- **Git**: These files are excluded from git (see `.gitignore`)
- **Replication**: To replicate the setup, ensure ZIP files are in `data/` and run the import scripts
- **Time**: ESCO import takes ~2-3 seconds, ONET import takes ~25-30 seconds
- **Language**: Currently only English (en) is imported for ESCO. Additional languages can be imported by running the script with different `--language` parameter
