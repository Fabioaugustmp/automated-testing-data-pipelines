# main.py
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field


# --- Pydantic Schema for MCC data ---
class MccEntry(BaseModel):
    """
    Pydantic model to define the structure of each MCC entry.
    """
    code: int = Field(..., example="5812", description="Merchant Category Code")
    description: str = Field(..., example="Eating Places, Restaurants", description="Description of the MCC")

# --- Global variable to store loaded MCC data ---
# This will hold the parsed JSON data once loaded.
mcc_data: Optional[List[MccEntry]] = None

# --- Function to load MCC data from JSON file ---
def load_mcc_data(file_path: str = "mcc.json") -> List[MccEntry]:
    """
    Loads MCC data from a specified JSON file.

    Args:
        file_path (str): The path to the JSON file containing MCC data.

    Returns:
        List[MccEntry]: A list of MccEntry objects parsed from the JSON file.

    Raises:
        HTTPException: If the file is not found or if there's a JSON decoding error.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Validate and parse each entry using the Pydantic model
        # This loop ensures that each item in the JSON list conforms to MccEntry
        parsed_data = [MccEntry(**item) for item in raw_data]
        return parsed_data

    except FileNotFoundError:
        # Raise an HTTPException if the file does not exist
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCC data file '{file_path}' not found. Please ensure it exists."
        )
    except json.JSONDecodeError:
        # Raise an HTTPException if the JSON is malformed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error decoding JSON from '{file_path}'. Check file format."
        )
    except Exception as e:
        # Catch any other unexpected errors during file processing
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while loading MCC data: {e}"
        )


# --- FastAPI Application Instance ---
app = FastAPI(
    title="MCC Lookup API",
    description="A simple API to retrieve Merchant Category Codes from a JSON file.",
    version="1.0.0"
)


# --- Event Handler to load data on application startup ---
@app.on_event("startup")
async def startup_event():
    """
    Loads MCC data when the FastAPI application starts up.
    This ensures the data is loaded once and available for all requests.
    """
    global mcc_data
    mcc_data = load_mcc_data()
    print(f"Loaded {len(mcc_data)} MCC entries from mcc.json")


# --- API Endpoints ---
@app.get("/mcc", response_model=List[MccEntry], tags=["MCC"])
def get_all_mcc_codes():
    """
    Retrieves all Merchant Category Codes and their descriptions.
    """
    # Check if data was loaded successfully during startup
    if mcc_data is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MCC data not loaded. Please check application logs for errors."
        )
    return mcc_data


@app.get("/mcc/{code}", response_model=MccEntry, tags=["MCC"])
def get_mcc_by_code(code: int):
    """
    Retrieves the description for a specific Merchant Category Code (MCC).
    - **code**: The 4-digit MCC to look up.
    """
    if mcc_data is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MCC data not loaded. Please check application logs for errors."
        )

    found_mcc = next((mcc for mcc in mcc_data if mcc.code == code), None)

    if found_mcc:
        return found_mcc
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCC '{code}' not found."
        )

