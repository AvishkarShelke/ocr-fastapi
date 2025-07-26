from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Optional: Allow cross-origin for APEX testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Step 1: Convert OCR output into simple key-value dict
def extract_fields_from_ocr(document_fields: list) -> dict:
    extracted_data = {}
    for field in document_fields:
        text = field.get("text")
        if "INR" in text or "USD" in text:
            extracted_data["Currency"] = text  # assuming the currency is part of the text
        elif "Total" in text or "Amount" in text:
            extracted_data["Total"] = text  # assuming total amount is part of the text
        elif "Purpose" in text:
            extracted_data["Purpose"] = text  # assuming purpose is captured in the OCR text
        elif "Y" in text or "Submit" in text:
            extracted_data["SubmitReport"] = "Y"
    return extracted_data

# Step 2: Normalize the extracted fields
def normalize_expense(data: dict) -> dict:
    return {
        "ReimbursementCurrencyCode": data.get("Currency", "INR"),
        "ExpenseReportTotal": data.get("Total", "0.00"),
        "Purpose": data.get("Purpose", "Not Mentioned"),
        "SubmitReport": data.get("SubmitReport", "N")
    }

@app.post("/extract")
async def extract_expense(req: Request):
    body = await req.json()

    # Extract fields based on the OCR output
    if "documentFields" in body:
        raw_data = extract_fields_from_ocr(body["documentFields"])
    else:
        raw_data = body  # fallback to simple format if needed

    return normalize_expense(raw_data)
