# Data Setup Guide

## Downloading Source Data

### ESCO Data

1. **Visit ESCO Portal**: https://ec.europa.eu/esco/portal
2. **Download Classification Files**: 
   - Go to "Download" section
   - Download CSV classification files for desired languages
   - Files are typically named: `classification_en.zip`, `classification_it.zip`, etc.
3. **Place in `data/` directory**:
   ```
   data/
   ├── esco_classification_en.zip
   ├── esco_classification_it.zip
   └── ...
   ```

**Required Files Inside ZIP:**
- `occupations_{language}.csv` - Occupation data
- `skills_{language}.csv` - Skill data
- `occupationSkillRelations_{language}.csv` - Occupation-skill relations

### ONET Data

1. **Visit ONET Resource Center**: https://www.onetcenter.org/database.html
2. **Download Database Files**:
   - Register for free account
   - Download "O*NET 30.1 Database" (or latest version)
   - Download "Text Database" format
3. **Place in `data/` directory**:
   ```
   data/
   └── db_30_1_text.zip
   ```

**Required Files Inside ZIP:**
- `db_30_1_text/Occupation Data.txt` - Occupation data
- `db_30_1_text/Task Statements.txt` - Task descriptions (task_id, task text)
- `db_30_1_text/Task Ratings.txt` - Occupation x task ratings (IM scale)
- `db_30_1_text/Technology Skills.txt` - Occupation x technology (software/tool) with Hot Technology / In Demand

---

## Creating Databases

### ESCO Database

```bash
# Create and import English data
python scripts/import_esco.py \
    --zip_path data/esco_classification_en.zip \
    --db_path data/esco.db \
    --language en

# Import additional languages (optional)
python scripts/import_esco.py \
    --zip_path data/esco_classification_it.zip \
    --db_path data/esco.db \
    --language it
```

**What it does:**
1. Creates `data/esco.db` SQLite database with schema
2. Extracts ZIP file to temporary directory
3. Imports occupations, skills, and relations from CSV files
4. Commits all data to database

**Options:**
- `--skip-skills`: Skip importing skills (faster, for initial setup)
- `--skip-relations`: Skip importing occupation-skill relations

### ONET Database

```bash
# Create and import data (use --recreate to replace existing DB with new schema)
python scripts/import_onet.py \
    --zip_path data/db_30_1_text.zip \
    --db_path data/onet.db \
    --recreate
```

**What it does:**
1. Creates `data/onet.db` SQLite database with schema
2. Extracts ZIP file to temporary directory
3. Imports occupations from Occupation Data.txt
4. Imports tasks from Task Statements.txt and occupation-task ratings (IM scale) from Task Ratings.txt
5. Imports technology skills from Technology Skills.txt and occupation-technology_skill relations (weight derived from Hot Technology / In Demand)
6. Commits all data to database

**Options:**
- `--recreate`: Delete existing database and create from schema (required when switching to tasks/tech skills)
- `--skip-tasks`: Skip importing tasks and occupation-task ratings
- `--skip-tech-skills`: Skip importing technology skills and occupation-technology_skill relations

---

## Verification

### Check ESCO Database

```bash
sqlite3 data/esco.db "SELECT COUNT(*) FROM esco_occupation WHERE language='en';"
sqlite3 data/esco.db "SELECT COUNT(*) FROM esco_skill WHERE language='en';"
sqlite3 data/esco.db "SELECT COUNT(*) FROM esco_occupation_skill;"
```

**Expected Results:**
- Occupations: ~3,000-4,000 per language
- Skills: ~13,000-14,000 per language
- Relations: ~100,000-150,000 total

### Check ONET Database

```bash
sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_occupation;"
sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_task;"
sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_occupation_task WHERE scale_id='IM';"
sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_technology_skill;"
sqlite3 data/onet.db "SELECT COUNT(*) FROM onet_occupation_technology_skill;"
```

**Expected Results:**
- Occupations: ~1,000-1,100
- Tasks: ~18,000
- Occupation-task ratings (IM): ~17,000+
- Technology skills: ~8,700
- Occupation-technology_skill relations: ~32,000

---

## Database Schema

### ESCO Tables

- `esco_occupation`: Occupations with URI, language, title, description
- `esco_skill`: Skills with URI, language, title, skill_type
- `esco_occupation_skill`: Relations between occupations and skills

### ONET Tables

- `onet_occupation`: Occupations with code, title, description
- `onet_task`: Tasks with task_id, task_text (from Task Statements)
- `onet_occupation_task`: Occupation x task relations with scale_id (IM) and data_value (importance)
- `onet_technology_skill`: Technology skills (example name, commodity_code, commodity_title)
- `onet_occupation_technology_skill`: Occupation x technology_skill relations with derived weight

---

## Troubleshooting

### ZIP File Not Found

**Error:** `ZIP file not found: data/esco_classification_en.zip`

**Solution:** 
- Verify ZIP file is in `data/` directory
- Check file name matches exactly (case-sensitive)

### Database Already Exists

**Note:** If database already exists, the import script will:
- Use existing database
- Update existing records
- Insert new records
- Skip duplicates (based on unique constraints)

### Missing CSV Files in ZIP

**Error:** `File not found: occupations_en.csv`

**Solution:**
- Verify ZIP file contains required CSV files
- Check language code matches (en, it, de, es, fr)
- Extract ZIP manually to verify contents

### Import Errors

**Common Issues:**
- **Encoding errors**: Ensure CSV files are UTF-8 encoded
- **Memory errors**: Process in smaller batches (modify batch_size in script)
- **Foreign key errors**: Import occupations and skills before relations

---

## Notes

- **Database Size**: 
  - ESCO: ~50-100 MB per language
  - ONET: ~10-20 MB
  
- **Import Time**:
  - ESCO: 2-5 minutes per language
  - ONET: 3-8 minutes

- **Storage**: Ensure sufficient disk space for databases and temporary extraction

---

**Ready to train models!** Once databases are created, proceed to training:

```bash
python examples/train_esco.py --db_path data/esco.db --output_dir models
```
