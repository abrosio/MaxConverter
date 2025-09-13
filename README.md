# MaxConverter – Photometric Log Extractor

MaxConverter is a **PyQt5 desktop application** that extracts photometric log data from CSV or TXT files (e.g., MaximDL outputs).  
It generates clean, fixed-width aligned text files with user-selectable output columns.

---

## Features

- **Input formats**: CSV (`.csv`) and plain text (`.txt`) logs  
  (supports MaximDL style and whitespace-separated files).  
- **Robust parser**:  
  - Reads comma-separated or whitespace-separated values.  
  - Fallback: extracts the first three numeric tokens (HJD, MAG, MAG_ERR).  
- **Output formatting**:  
  - Fixed-width aligned columns.  
  - Headers exactly aligned with data.  
- **Selectable columns**:  
  - `NAME`, `HJD`, `MAG`, `MAG_ERR`, `FILTER`.  
  - Defaults: `HJD`, `MAG`, `MAG_ERR`.  
- **Compact GUI**:  
  - File picker with Desktop as default directory.  
  - Checkbox controls under an *Outputs* label.  
  - Extract button for saving output.  
- **Absolute icon loading**:  
  - Uses `icon.ico` from the same folder as the program.  

---

