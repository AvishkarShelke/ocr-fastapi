from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import json

app = FastAPI()

# Step 3: Define the expected format using Pydantic (for clarity/validation if needed)
class ExpenseRequest(BaseModel):
    ReimbursementCurrencyCode: str
    ExpenseReportTotal: str
    Purpose: str
    SubmitReport: str

# Optional: Normalize input JSON fields from multiple formats
def normalize_expense(data):
    return {
        "ReimbursementCurrencyCode": data.get("Currency") or data.get("ReimbursementCurrencyCode", "INR"),
        "ExpenseReportTotal": str(data.get("Total") or data.get("ExpenseReportTotal", "0")),
        "Purpose": data.get("Purpose", "General"),
        "SubmitReport": data.get("SubmitReport", "Y")
    }

# Step 4: API endpoint to receive and process the uploaded JSON file
@app.post("/convert-expense/")
async def convert_expense(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8"))

        # Clean and normalize the data to match fixed format
        formatted_output = normalize_expense(data)

        return formatted_output

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

