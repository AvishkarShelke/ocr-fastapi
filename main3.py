from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import JSONResponse
import json
import os
import re
import shutil

app = FastAPI()

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

latest_uploaded_file = None

# -------------------- Upload OCR File --------------------
@app.post("/upload-json")
async def upload_json(file: UploadFile = File(...)):
    global latest_uploaded_file

    if not file.filename.endswith(".json") and not file.filename.endswith(".txt"):
        return JSONResponse(content={"error": "Only .json or .txt allowed"}, status_code=400)

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    latest_uploaded_file = file_path
    return {"message": "File uploaded successfully", "file_path": file_path}

# -------------------- Load OCR Words --------------------
def load_words_from_file():
    if not latest_uploaded_file:
        raise Exception("No OCR file uploaded yet.")

    with open(latest_uploaded_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["pages"][0].get("words", [])

# -------------------- Extract Total Amount --------------------
def extract_total_amount(words: list) -> float:
    lines = []
    current_line = []
    prev_y = None

    for word in sorted(words, key=lambda w: w['boundingPolygon']['normalizedVertices'][0]['y']):
        y = round(word['boundingPolygon']['normalizedVertices'][0]['y'], 2)
        if prev_y is None or abs(y - prev_y) < 0.01:
            current_line.append(word["text"])
        else:
            lines.append(" ".join(current_line))
            current_line = [word["text"]]
        prev_y = y
    if current_line:
        lines.append(" ".join(current_line))

    # Search for totals with priority keywords
    priority_keywords = r"(food\s*total|grand\s*total|net\s*payable|invoice\s*total|total)"
    amounts = []

    for line in lines:
        if re.search(priority_keywords, line, re.IGNORECASE):
            matches = re.findall(r"\d{2,6}\.\d{2}", line)
            for amt in matches:
                amounts.append(float(amt))

    # Fallback: take max numeric value
    if not amounts:
        all_matches = re.findall(r"\d{2,6}\.\d{2}", " ".join(lines))
        amounts = [float(a) for a in all_matches]

    return max(amounts) if amounts else 0.0

# -------------------- Smart Auto-Fill Report --------------------
@app.post("/correct-report")
async def correct_expense_report():
    try:
        words = load_words_from_file()
        total = extract_total_amount(words)
        full_text = " ".join([word["text"] for word in words]).upper()

        # --- Currency Detection ---
        if "INR" in full_text or "₹" in full_text:
            currency = "INR"
        elif "USD" in full_text or "$" in full_text:
            currency = "USD"
        elif "EUR" in full_text or "€" in full_text:
            currency = "EUR"
        else:
            currency = "INR"

        # --- Purpose Detection ---
        if "DMART" in full_text:
            purpose = "DMart Shopping"
        elif any(keyword in full_text for keyword in ["PETROL", "FUEL", "HPCL", "IOC"]):
            purpose = "Fuel Reimbursement"
        elif any(keyword in full_text for keyword in ["HOTEL", "RESTAURANT", "CAFE", "FOOD"]):
            purpose = "Food/Hotel Expense"
        elif "MEDICAL" in full_text or "PHARMACY" in full_text:
            purpose = "Medical Reimbursement"
        else:
            purpose = "General Reimbursement"

        # --- Submit Flag ---
        submit = "Y"

        return {
            "ReimbursementCurrencyCode": currency,
            "ExpenseReportTotal": f"{total:.2f}",
            "Purpose": purpose,
            "SubmitReport": submit
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


