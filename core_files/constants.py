from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize constants from environment variables
API_KEY = os.getenv('API_KEY')
LEETCODE_CLIENT_URL = os.getenv('LEETCODE_CLIENT_URL')
LEETCODE_HOST = os.getenv('LEETCODE_HOST')
LEETCODE_PORT = os.getenv('LEETCODE_PORT')
MAIN_URL = os.getenv('MAIN_URL')
MAIN_HOST = os.getenv('MAIN_HOST')
MAIN_PORT = os.getenv('MAIN_PORT')

# Keep the query in constants as it's not sensitive
USERNAME_QUERY="""
        query getUserQuestionStats($userSlug:String!){
            userProfileUserQuestionProgressV2(userSlug: $userSlug){
                numAcceptedQuestions{
                        difficulty
                        count
                        }
                }
            }
         """