import ssl
import certifi
import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
import logging
import constants
import traceback  # Import traceback for detailed error logging

logging.basicConfig(
    filename="leetcode_client.log",  # Log file name
    level=logging.ERROR,  # Log only INFO and above
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

PORT = constants.LEETCODE_PORT
HOST = constants.LEETCODE_HOST

app = FastAPI()
ssl_context = ssl.create_default_context(cafile=certifi.where())
leetCodeUrl = "https://leetcode.com/graphql"

# pass json to parameters

@app.get("/{username}")
async def get_user_stats(username: str):
    query = constants.USERNAME_QUERY
    variables = {"userSlug": username}
    headers = {
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session:
            async with session.post(
                leetCodeUrl,
                headers=headers,
                json={"query": query, "variables": variables},
            ) as response:
                if response.status == 200: # successful request
                    data = await response.json()
                    if "errors" in data: # error parsing the data from the response
                        raise HTTPException(
                            status_code=404, detail="user cannot be found"
                        )
                    userStats = data["data"]["userProfileUserQuestionProgressV2"]["numAcceptedQuestions"]
                    return {
                        entry["difficulty"]: entry["count"] for entry in userStats
                    }

                else:
                    # Log the status code and response text for debugging
                    detail = await response.text()
                    logging.error(f"Status code: {response.status}, Response: {detail}")
                    raise HTTPException(status_code=response.status, detail=detail)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Exception: {e}, Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error occurred: {e}")

if __name__ == "__main__":
    print(f"LeetCode Client running on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="error", use_colors=False)
