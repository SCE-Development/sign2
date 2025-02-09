from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
import aiohttp
import ssl

# Constants for API Key
import constants  # Ensure this contains a list or set of valid API keys

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

# API Key validation function
def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:

    if api_key_header in constants.API_KEY:
        print("API Key validated via header.")
        return api_key_header
    elif api_key_query in constants.API_KEY:
        print("API Key validated via query.")
        return api_key_query
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or Missing API Key"
        )