from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Normalize the extracted fields
def normalize_expense(data: dict) -> dict:
    return {
        "ReimbursementCurrencyCode": data.get("Currency", "INR"),
        "ExpenseReportTotal": data.get("Total", "0.00"),
        "Purpose": data.get("Purpose", "Not Mentioned"),
        "SubmitReport": data.get("SubmitReport", "N")
    }

# Function to extract the relevant fields from Oracle DU OCR document
def extract_fields_from_ocr(document_fields: list) -> dict:
    extracted_data = {}

    for field in document_fields:
        text = field.get("text", "").strip()

        # Look for currency (e.g., INR or USD)
        if "INR" in text or "USD" in text:
            extracted_data["Currency"] = text
        
        # Look for total amount or similar (e.g., "432.60")
        elif any(keyword in text for keyword in ["Total", "Amount", "₹"]):
            extracted_data["Total"] = text.strip()  # Clean amount

        # Look for purpose (e.g., "Fuel Reimbursement")
        elif "Fuel" in text or "Hotel" in text or "DMart" in text:  # Add more cases if needed
            extracted_data["Purpose"] = text.strip()

        # Handle "Submit" or "Y" for the flag
        elif "Submit" in text or "Y" in text:
            extracted_data["SubmitReport"] = "Y"
    
    return extracted_data

@app.post("/extract")
async def extract_expense(req: Request):
    body = await req.json()

    # Extract fields based on the OCR output
    if "documentFields" in body:
        raw_data = extract_fields_from_ocr(body["documentFields"])
    else:
        raw_data = body  # Fallback to simple format if needed

    return normalize_expense(raw_data)
