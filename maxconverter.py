"""
MaxConverter
----------------------------------------
Author: Antonino Brosio (www.antoninobrosio.it)
License: GNU GENERAL PUBLIC LICENSE
Description:
    PyQt5 GUI application for extracting photometric log data (HJD, MAG, MAG_ERR, etc.)
    from CSV/TXT files (e.g. MaximDL output). Provides fixed-width aligned output
    with optional columns selected via checkboxes.

Features:
    - Robust parser: supports CSV, whitespace, or numeric token fallback.
    - Output formatting: fixed-width table with headers aligned with data.
    - GUI: file picker, checkboxes for optional columns, extract button.
    - Defaults: HJD, MAG, MAG_ERR always enabled by default.
    - Icon: uses local icon.ico in the same folder as the script.
    - Optional observer codes: MPC and/or AAVSO fields; when provided, default
      output filename becomes BASE_YYYYMMDD_AAVSO.txt or BASE_YYYYMMDD_MPC.txt
      (otherwise BASE_YYYYMMDD.txt).
"""

import os
import sys
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List

from PyQt5 import QtWidgets, QtGui, QtCore

APP_TITLE = "MaxConverter"

# ---------------------------
# Utilities
# ---------------------------

# Regex pattern for generic floating-point tokens (captures scientific notation too)
FLOAT_TOKEN = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
float_re = re.compile(FLOAT_TOKEN)

# Available output columns
ALL_COLUMNS = ["NAME", "HJD", "MAG", "MAG_ERR", "FILTER"]
# Columns enabled by default
DEFAULT_COLUMNS = ["HJD", "MAG", "MAG_ERR"]


def desktop_dir() -> str:
    """
    Returns the user's Desktop directory if available, otherwise the home directory.
    Used as the default location for file dialogs.
    """
    d = os.path.join(os.path.expanduser("~"), "Desktop")
    return d if os.path.isdir(d) else os.path.expanduser("~")


def jd_to_yyyymmdd(jd_value: str) -> str:
    """Convert a Julian Date string to YYYYMMDD. Returns today if conversion fails."""
    try:
        jd = float(str(jd_value).strip())
        dt = datetime(2000, 1, 1, 12, 0, 0) + timedelta(days=jd - 2451545.0)
        return dt.strftime("%Y%m%d")
    except Exception:
        return date.today().strftime("%Y%m%d")


def sanitize_filename_part(value: str) -> str:
    """Normalize a filename part: uppercase, trim, replace spaces, remove invalid chars."""
    s = str(value).strip().upper().replace(" ", "_")
    s = re.sub(r'[^A-Z0-9_\-]+', '', s)
    return s


def parse_line_to_fields(line: str) -> dict:
    """
    Parse a single line of input and return a dict with possible keys:
    NAME, HJD, MAG, MAG_ERR, FILTER.

    Supports:
        - CSV with commas
        - Space/tab separated values
        - Fallback: extracts first three numeric tokens as HJD, MAG, MAG_ERR
    """
    s = line.strip()
    if not s or s.startswith("#"):
        return {}

    # CSV (comma-separated)
    parts = s.split(",")
    if len(parts) >= 5:
        return {
            "NAME": parts[0].strip(),
            "HJD": parts[1].strip(),
            "MAG": parts[2].strip(),
            "MAG_ERR": parts[3].strip(),
            "FILTER": parts[4].strip(),
        }

    # Whitespace-separated (e.g., MaximDL TXT export)
    parts = re.split(r"\s+", s)
    if len(parts) >= 5:
        return {
            "NAME": parts[0].strip(),
            "HJD": parts[1].strip(),
            "MAG": parts[2].strip(),
            "MAG_ERR": parts[3].strip(),
            "FILTER": parts[4].strip(),
        }

    # Fallback: extract first 3 numeric tokens
    nums = float_re.findall(s)
    if len(nums) >= 3:
        return {"NAME": "", "HJD": nums[0], "MAG": nums[1], "MAG_ERR": nums[2], "FILTER": ""}

    return {}


def extract_data(input_path: str) -> List[dict]:
    """
    Parse all lines in a given file and return a list of dictionaries
    with the extracted photometric data.
    """
    out: List[dict] = []
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            row = parse_line_to_fields(raw)
            if row:
                out.append(row)
    return out


def format_table(rows: List[dict], selected_cols: List[str]) -> str:
    """
    Format a list of dict records into a fixed-width text table.

    - Each column width is determined by the longest value or header + extra spacing.
    - Headers are aligned with the corresponding column values.
    - Returns the complete table as a string ready to be written to a TXT file.
    """
    widths = {}
    for col in selected_cols:
        max_len = max([len(str(r.get(col, ""))) for r in rows] + [len(col)])
        widths[col] = max_len + 3  # add padding for readability

    # Header row
    header = "".join(col.ljust(widths[col]) for col in selected_cols)

    # Data rows
    lines = []
    for r in rows:
        line = "".join(str(r.get(col, "")).ljust(widths[col]) for col in selected_cols)
        lines.append(line)

    return "\n".join([header] + lines)


# ---------------------------
# GUI
# ---------------------------
class MainWindow(QtWidgets.QWidget):
    """
    Main application window for MaxConverter.
    Provides file selection, output column options, optional observer codes,
    and the extraction action.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)

        # Load absolute icon from same folder as script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        # Window size
        self.resize(720, 190)

        # Enable drag and drop of input files onto the window
        self.setAcceptDrops(True)

        # --- Input row: file path + browse button ---
        self.input_edit = QtWidgets.QLineEdit(self)
        self.input_edit.setPlaceholderText("Path to CSV/TXT file to convert…")
        self.browse_btn = QtWidgets.QPushButton("Browse", self)
        self.browse_btn.clicked.connect(self.on_browse_input)

        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.browse_btn)

        # --- Outputs section ---
        outputs_label = QtWidgets.QLabel("Outputs", self)
        outputs_label.setStyleSheet("font-weight: bold;")

        # Checkboxes for column selection
        self.checks = {}
        checks_layout = QtWidgets.QHBoxLayout()
        for col in ALL_COLUMNS:
            cb = QtWidgets.QCheckBox(col, self)
            cb.setChecked(col in DEFAULT_COLUMNS)
            self.checks[col] = cb
            checks_layout.addWidget(cb)

        # Small spacing below checkboxes
        # (allows a little breathing room before the codes row)
        codes_top_spacer = QtWidgets.QSpacerItem(0, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        # --- Observer codes (MPC / AAVSO) under checkboxes ---
        codes_layout = QtWidgets.QHBoxLayout()
        codes_layout.addWidget(QtWidgets.QLabel("MPC:", self))
        self.mpc_edit = QtWidgets.QLineEdit(self)
        self.mpc_edit.setPlaceholderText("MPC code (optional)")
        self.mpc_edit.setFixedWidth(160)  # slightly longer so placeholder isn't clipped
        codes_layout.addWidget(self.mpc_edit)

        codes_layout.addSpacing(10)
        codes_layout.addWidget(QtWidgets.QLabel("AAVSO:", self))
        self.aavso_edit = QtWidgets.QLineEdit(self)
        self.aavso_edit.setPlaceholderText("AAVSO code (optional)")
        self.aavso_edit.setFixedWidth(160)
        codes_layout.addWidget(self.aavso_edit)

        codes_layout.addSpacing(10)
        codes_layout.addWidget(QtWidgets.QLabel("Filter:", self))
        self.filter_edit = QtWidgets.QLineEdit(self)
        self.filter_edit.setPlaceholderText("Filter for filename (optional)")
        self.filter_edit.setFixedWidth(120)
        codes_layout.addWidget(self.filter_edit)
        codes_layout.addStretch(1)

        # --- Extract button ---
        self.extract_btn = QtWidgets.QPushButton("Extract", self)
        self.extract_btn.setEnabled(False)
        self.extract_btn.clicked.connect(self.on_extract)

        # Enable/disable Extract button based on input field content
        self.input_edit.textChanged.connect(self.on_input_changed)

        # --- Layout assembly ---
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(input_layout)
        layout.addWidget(outputs_label)
        layout.addLayout(checks_layout)
        layout.addItem(codes_top_spacer)
        layout.addLayout(codes_layout)
        layout.addSpacing(10)  # push Extract button slightly lower
        layout.addWidget(self.extract_btn, alignment=QtCore.Qt.AlignRight)

    # ---------------------------
    # Slots / Event Handlers
    # ---------------------------


    def dragEnterEvent(self, event):
        """Accept drag-and-drop when it contains at least one local file."""
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile() and os.path.isfile(url.toLocalFile()):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Load the first dropped local file into the input field automatically."""
        mime = event.mimeData()
        if not mime.hasUrls():
            event.ignore()
            return

        for url in mime.urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    self.input_edit.setText(file_path)
                    event.acceptProposedAction()
                    return

        event.ignore()

    def on_input_changed(self, text: str):
        """Enable Extract button only if the given path points to a valid file."""
        self.extract_btn.setEnabled(os.path.isfile(text))

    def on_browse_input(self):
        """Open a file dialog to choose a CSV/TXT input file (default: Desktop)."""
        start_dir = desktop_dir()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select photometric log file",
            start_dir,
            "Photometric logs (*.csv *.txt);;All files (*.*)",
        )
        if path:
            self.input_edit.setText(path)

    def _default_filename(self, in_path: str, rows: List[dict]) -> str:
        """
        Build the default output filename in the form:
        OBJECT_YYYYMMDD_FILTER_CODE.txt

        Where:
        - OBJECT is the input stem uppercased, spaces replaced with underscores
        - YYYYMMDD is derived from the HJD/JD of the first observation
        - FILTER is read from the dedicated GUI field
        - CODE is the AAVSO code if present, otherwise the MPC code
        """
        in_stem = Path(in_path).stem
        base = sanitize_filename_part(in_stem)

        first_hjd = rows[0].get("HJD", "") if rows else ""
        date_str = jd_to_yyyymmdd(first_hjd)

        filter_part = sanitize_filename_part(self.filter_edit.text())
        code_part = sanitize_filename_part(self.aavso_edit.text() or self.mpc_edit.text())

        parts = [p for p in [base, date_str, filter_part, code_part] if p]
        return "_".join(parts) + ".txt"

    def on_extract(self):
        """Handle the extraction process and save results to a TXT file."""
        in_path = self.input_edit.text().strip()
        if not os.path.isfile(in_path):
            QtWidgets.QMessageBox.warning(self, APP_TITLE, "Please select a valid file.")
            return

        try:
            rows = extract_data(in_path)
            if not rows:
                QtWidgets.QMessageBox.warning(self, APP_TITLE, "No data found in file.")
                return
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, APP_TITLE, f"Error while reading: {e}")
            return

        # Columns selected by user
        selected_cols = [c for c, cb in self.checks.items() if cb.isChecked()]
        if not selected_cols:
            QtWidgets.QMessageBox.warning(self, APP_TITLE, "Select at least one column.")
            return

        # Format output
        text_out = format_table(rows, selected_cols)

        # Suggest default output filename (Desktop as default directory)
        start_dir = desktop_dir()
        default_path = str(Path(start_dir) / self._default_filename(in_path, rows))

        # Save dialog
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save extracted file",
            default_path,
            "Text files (*.txt)",
        )
        if not out_path:
            return

        # Write result to file
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text_out)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, APP_TITLE, f"Error while writing: {e}")
            return

        QtWidgets.QMessageBox.information(
            self, APP_TITLE, f"File saved successfully:\n{out_path}"
        )


def main():
    """
    Application entry point.
    Initializes Qt, sets high-DPI attributes, and shows the main window.
    """
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
