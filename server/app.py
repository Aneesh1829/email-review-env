
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server import create_app
from models import EmailAction, EmailObservation
from server.environment import EmailReviewEnvironment

# Use a factory FUNCTION so each WebSocket session
# gets its own completely fresh environment instance
def make_env():
    return EmailReviewEnvironment()

app = create_app(
    make_env,
    EmailAction,
    EmailObservation,
    env_name="email_review_env"
)
