from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import pandas as pd
from app.services.chainladder_service import ChainladderService

router = APIRouter()
chainladder_service = ChainladderService()


@router.post("/analyze")
async def analyze_triangle(
    csv: UploadFile = File(...),
    origin_col: str = Form("origin"),
    dev_col: str = Form("dev"),
    value_col: str = Form("value"),
    cumulative: bool = Form(True),
):
    """
    Analyze a loss triangle using chainladder methods.

    Accepts a CSV file with columns for origin period, development period, and values.
    Returns Mack Chainladder, Cape Cod, and age-to-age LDF results.
    """
    try:
        # Validate file type
        if not csv.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        # Read CSV file
        df = pd.read_csv(csv.file)

        # Validate required columns exist
        if origin_col not in df.columns:
            raise HTTPException(
                status_code=400, detail=f"Column '{origin_col}' not found in CSV"
            )
        if dev_col not in df.columns:
            raise HTTPException(
                status_code=400, detail=f"Column '{dev_col}' not found in CSV"
            )
        if value_col not in df.columns:
            raise HTTPException(
                status_code=400, detail=f"Column '{value_col}' not found in CSV"
            )

        # Analyze triangle using chainladder service
        result = chainladder_service.analyze_triangle(
            df, origin_col, dev_col, value_col, cumulative
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing triangle: {str(e)}"
        )
