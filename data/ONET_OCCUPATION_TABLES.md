# Tabelle O*NET (db_30_1_text) in relazione con le occupazioni

Nel database O*NET 30.1 (`db_30_1_text.zip`) la tabella **Skills.txt** contiene solo **35 elementi** (il content model "Skills" in senso stretto). Le **migliaia di skills** paragonabili a ESCO (~14.000) in O*NET hanno **denominazioni diverse** e sono in altre tabelle.

## Tabelle con relazione Occupation × Elemento

Tutte usano **O*NET-SOC Code** come chiave occupazione. Conti fatti sui file estratti da `db_30_1_text.zip`.

| File | Cosa contiene | Elementi unici | Relazione | Scale / note |
|------|----------------|-----------------|-----------|---------------|
| **Skills.txt** | Skills (content model) | **35** | occupation × Element ID | IM (Importance), LV (Level) |
| Abilities.txt | Abilità | 52 | occupation × Element ID | IM, LV |
| Knowledge.txt | Conoscenze | 33 | occupation × Element ID | IM, LV |
| Work Activities.txt | Attività di lavoro | 41 | occupation × Element ID | IM, LV |
| Work Context.txt | Contesto di lavoro | 57 | occupation × Element ID | CX, CXP, ecc. |
| Work Styles.txt | Stili di lavoro | 21 | occupation × Element ID | DR, ecc. |
| **Task Ratings.txt** | Rating dei task | **~18.000** Task ID | occupation × Task ID | FT (Frequency), RT (Relevance), ecc. |
| **Task Statements.txt** | Descrizione task | ~18.800 task | lookup Task ID → testo | Colonna "Task" |
| **Technology Skills.txt** | Software/tool per occupazione | **~8.785** Example | occupation × Example | Hot Technology, In Demand (Y/N) |
| **Tools Used.txt** | Strumenti/attrezzature | **~18.105** Example | occupation × Example | Commodity Code, Commodity Title |

## Corrispondente “reale” delle migliaia di skills ESCO

- **ESCO**: ~14.000 skills, legate alle occupazioni da relazioni occupation–skill.
- **O*NET**: il content model “Skills” ha solo 35 elementi; i **corrispondenti in ordine di grandezza** sono:

1. **Tasks** (Task Ratings + Task Statements)  
   - **~18.000** task unici, descritti in linguaggio naturale in **Task Statements.txt**.  
   - Per ogni occupazione ci sono rating (es. Frequency, Relevance) in **Task Ratings.txt**.  
   - È il candidato più vicino a “migliaia di competenze/attività” come in ESCO.

2. **Technology Skills**  
   - **~8.785** voci (nome software/tool).  
   - Relazione occupation × technology (Y/N per Hot Technology, In Demand).  
   - Utile per “skill” in senso tecnologico.

3. **Tools Used**  
   - **~18.105** voci (strumenti, attrezzature).  
   - Relazione occupation × tool; meno “skill” e più “strumenti usati”.

## Struttura file principali

- **Skills.txt** (e Abilities, Knowledge, Work Activities):  
  `O*NET-SOC Code` | `Element ID` | `Element Name` | `Scale ID` | `Data Value` | …

- **Task Ratings.txt**:  
  `O*NET-SOC Code` | `Task ID` | `Scale ID` | `Category` | `Data Value` | …

- **Task Statements.txt**:  
  `O*NET-SOC Code` | `Task ID` | `Task` (testo) | `Task Type` | …

- **Technology Skills.txt**:  
  `O*NET-SOC Code` | `Example` | `Commodity Code` | `Commodity Title` | `Hot Technology` | `In Demand`

- **Tools Used.txt**:  
  `O*NET-SOC Code` | `Example` | `Commodity Code` | `Commodity Title`

Per un sistema di raccomandazione con **migliaia di “skills”** su O*NET ha senso usare **Tasks** (e opzionalmente **Technology Skills** / **Tools Used**) invece del solo **Skills.txt** a 35 elementi.
