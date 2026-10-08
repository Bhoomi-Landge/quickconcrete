"""Parse supplier rate sheets from CSV or OCR text."""

import csv
import io
import re
import shutil

from services.plant_service import PlantError

GRADE_PATTERN = re.compile(
    r"^(M[\-\d\.]+(?:\s+(?:PILE|FF))?)",
    re.I,
)
PRICE_NUMBER = re.compile(r"\b(\d{3,5})\b")


def _plant_location_hints(plant):
    if not plant:
        return []
    parts = [
        getattr(plant, "plant_name", "") or "",
        getattr(plant, "city", "") or "",
        getattr(plant, "address", "") or "",
        getattr(plant, "pincode", "") or "",
    ]
    text = " ".join(parts).lower()
    tokens = re.findall(r"[a-z0-9]{3,}", text)
    # Useful aliases for Mumbai rate sheets
    aliases = []
    if any(x in text for x in ("turbhe", "vashi", "nerul", "kharghar", "panvel", "navi")):
        aliases.extend(["navi", "thane", "kalyan"])
    if "mumbai" in text and "south" not in text:
        aliases.append("mumbai")
    if any(x in text for x in ("worli", "mahim", "dadar", "santacruz", "bandra")):
        aliases.extend(["worli", "mahim", "dadar", "santacruz", "sntacruz"])
    if any(x in text for x in ("colaba", "fort", "churchgate", "nariman")):
        aliases.extend(["south", "bombay"])
    if any(x in text for x in ("mulund", "ghatkopar", "chembur", "sion", "kandivali")):
        aliases.extend(["mulund", "ghatkopar", "chembur", "sion", "kandivali"])
    return list(dict.fromkeys(tokens + aliases))


def _score_header_match(header_cell, hints):
    h = (header_cell or "").lower()
    if not h.strip():
        return 0
    score = 0
    for hint in hints:
        if len(hint) < 3:
            continue
        if hint in h:
            score += len(hint) + 10
    return score


def pick_price_column_index(location_headers, plant):
    """0-based index into location_headers (price columns only, not grade)."""
    hints = _plant_location_hints(plant)
    if not location_headers:
        return 0
    if len(location_headers) == 1:
        return 0
    best_idx = 0
    best_score = -1
    for idx, header in enumerate(location_headers):
        s = _score_header_match(header, hints)
        if s > best_score:
            best_score = s
            best_idx = idx
    return best_idx


def _rows_from_grade_price_pairs(pairs):
    rows = []
    for grade, price in pairs:
        grade = (grade or "").strip().upper()
        if not grade or grade == "GRADE":
            continue
        try:
            price = float(str(price).replace(",", "").strip())
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        rows.append({"grade": grade, "price_per_m3": round(price, 2)})
    if not rows:
        raise PlantError("No valid grade/price rows found in file.")
    return rows


def parse_csv_rate_rows(file_bytes, plant=None):
    text = file_bytes.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    all_rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not all_rows:
        raise PlantError("CSV file is empty.")

    first = [c.strip() for c in all_rows[0]]
    first_col = (first[0] or "").upper()

    # Multi-column rate sheet: GRADE + region1 + region2 + ...
    if first_col.startswith("GRADE") and len(first) >= 3:
        col_idx = pick_price_column_index(first[1:], plant)
        pairs = []
        for row in all_rows[1:]:
            if len(row) < col_idx + 2:
                continue
            pairs.append((row[0], row[col_idx + 1]))
        return _rows_from_grade_price_pairs(pairs)

    # Two columns with optional header
    if first_col.startswith("GRADE") and len(first) >= 2:
        pairs = [(row[0], row[1]) for row in all_rows[1:] if len(row) >= 2]
        return _rows_from_grade_price_pairs(pairs)

    # Simple grade,price (no header)
    pairs = [(row[0], row[1]) for row in all_rows if len(row) >= 2]
    return _rows_from_grade_price_pairs(pairs)


def _parse_header_columns(line):
    """Return list of location header strings from a GRADE header line."""
    line = line.strip()
    if not line.upper().startswith("GRADE"):
        return []
    rest = line[5:].strip()
    if not rest:
        return []
    if "|" in rest:
        return [p.strip() for p in rest.split("|") if p.strip()]
    # Split on 2+ spaces or tab
    parts = re.split(r"\t|\s{2,}", rest)
    return [p.strip() for p in parts if p.strip()]


def parse_rate_sheet_text(text, plant=None):
    """
    Parse OCR/plain text from rate sheets.
    Picks the price column automatically from plant city/name vs header row.
    """
    lines = [(ln or "").strip() for ln in (text or "").splitlines() if (ln or "").strip()]
    if not lines:
        raise PlantError("Could not read any text from image. Try CSV or manual entry.")

    location_headers = []
    header_line_idx = None
    for idx, line in enumerate(lines[:8]):
        if line.upper().startswith("GRADE"):
            location_headers = _parse_header_columns(line)
            header_line_idx = idx
            break

    price_col_idx = pick_price_column_index(location_headers, plant) if location_headers else 0

    rows = []
    for line in lines:
        if line.upper().startswith("GRADE"):
            continue
        grade_match = GRADE_PATTERN.match(line)
        if not grade_match:
            continue
        grade = grade_match.group(1).strip().upper()
        numbers = [float(x.replace(",", "")) for x in PRICE_NUMBER.findall(line)]
        if not numbers:
            continue
        if len(numbers) <= price_col_idx:
            if len(numbers) == 1:
                price = numbers[0]
            else:
                continue
        else:
            price = numbers[price_col_idx]
        rows.append({"grade": grade, "price_per_m3": round(price, 2)})

    if not rows:
        raise PlantError(
            "Could not parse grades from image. Save as CSV (grade,price per line) or use manual import."
        )
    return rows


def ocr_image_to_text(file_bytes):
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise PlantError(
            "Image OCR is not set up on the server. Run: pip install Pillow pytesseract "
            "(in backend venv), or use CSV / manual lines."
        )
    if not shutil.which("tesseract"):
        raise PlantError(
            "Tesseract is not installed. Run: brew install tesseract — or upload a CSV instead."
        )
    image = Image.open(io.BytesIO(file_bytes))
    try:
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractError as exc:
        raise PlantError(f"OCR failed: {exc}") from exc


def parse_upload(file_bytes, filename, plant):
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return parse_csv_rate_rows(file_bytes, plant=plant)
    text = ocr_image_to_text(file_bytes)
    return parse_rate_sheet_text(text, plant=plant)
