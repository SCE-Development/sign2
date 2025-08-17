from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

import constants

api_key_query = APIKeyQuery(name="api-key", auto_error=True)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)

def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:

    if api_key_header in constants.API_KEY:
        return api_key_query

    if api_key_query in constants.API_KEY:
        return api_key_query
    else:
        print("Failed for query")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or Missing API Key"
    )
