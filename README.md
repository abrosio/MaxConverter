# MaxConverter

MaxConverter is a **PyQt5 desktop application** that extracts photometric log data from CSV or TXT files (e.g., MaximDL outputs).  
It generates clean, fixed-width aligned text files with user-selectable output columns.

---

## ✨ Features

- 📂 **Input formats**: CSV (`.csv`) and plain text (`.txt`) logs  
  (supports MaximDL style and whitespace-separated files).  
- 🧾 **Robust parser**:  
  - Reads comma-separated or whitespace-separated values.  
  - Fallback: extracts the first three numeric tokens (HJD, MAG, MAG_ERR).  
- 📊 **Output formatting**:  
  - Fixed-width aligned columns.  
  - Headers exactly aligned with data.  
- ✅ **Selectable columns**:  
  - `NAME`, `HJD`, `MAG`, `MAG_ERR`, `FILTER`.  
  - Defaults: `HJD`, `MAG`, `MAG_ERR`.  
- 🖥️ **Compact GUI**:  
  - File picker with Desktop as default directory.  
  - Checkbox controls under an *Outputs* label.  
  - Extract button for saving output.  
- 🛰️ **Observer codes (new)**:  
  - Two input fields allow you to specify your **MPC code** and/or **AAVSO code**.  
  - If one of these codes is provided, the default output filename will include it.  
    - Example with AAVSO code: `VEGA_20250101_AAVSO.txt`  
    - Example with MPC code: `VEGA_20250101_MPC.txt`  
  - If no codes are provided, the default naming format is `VEGA_20250101.txt`.  

---

## 👤 Author

Created by **Antonino Brosio**  
🌐 [www.antoninobrosio.it](http://www.antoninobrosio.it)  
🔭 **MPC CODE:** L90  
🌌 **AAVSO:** BANI

---
