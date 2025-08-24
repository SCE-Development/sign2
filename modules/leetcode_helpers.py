import dataclasses

import requests

from modules.logger import logger


LEETCODE_BASE_URL = "https://leetcode.com/graphql"
SOLVED_QUERY = """
    query getUserQuestionStats($userSlug:String!){
        userProfileUserQuestionProgressV2(userSlug: $userSlug){
            numAcceptedQuestions{
                difficulty
                count
            }
        }
    }
"""

DIFFICULTY_EASY = "EASY"
DIFFICULTY_MEDIUM = "MEDIUM"
DIFFICULTY_HARD = "HARD"


@dataclasses.dataclass
class LeetcodeSnapshot:
    user: str
    easy: int
    medium: int
    hard: int


def get_leetcode_problems_solved(username: str):
    variables = {"userSlug": username}
    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            LEETCODE_BASE_URL,
            headers=headers,
            json={"query": SOLVED_QUERY, "variables": variables},
            timeout=10,
        )

        if response.status_code != 200:
            logger.warning(
                f"received non 200 response {response.status_code} for user {username}"
            )
            return None
        data = response.json()
        if data.get("errors"):
            errors = data.get("errors")
            logger.warning(
                f"non empty errors object for username {username}: {errors}"
            )
            return None

        user_stats = (
            data.get("data", {})
            .get("userProfileUserQuestionProgressV2", {})
            .get("numAcceptedQuestions", [])
        )
        if not user_stats:
            return None

        difficulty_mapping = {
            DIFFICULTY_EASY: 0,
            DIFFICULTY_MEDIUM: 0,
            DIFFICULTY_HARD: 0,
        }

        for entry in user_stats:
            if not isinstance(entry, dict):
                logger.warning(
                    f"entry was not a dict for username {username}! value: {entry}"
                )
                continue
            difficulty = entry.get("difficulty", "").upper()
            count = entry.get("count", 0)

            if difficulty in [DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD]:
                difficulty_mapping[difficulty] = count
                continue
            logger.warning(
                f"for username {username}, unknown difficulty key {difficulty} in entry {entry}"
            )
        return LeetcodeSnapshot(
            user=username,
            easy=difficulty_mapping[DIFFICULTY_EASY],
            medium=difficulty_mapping[DIFFICULTY_MEDIUM],
            hard=difficulty_mapping[DIFFICULTY_HARD],
        )
    except Exception:
        logger.exception("no!")
