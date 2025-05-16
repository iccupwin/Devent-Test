import os
import posthog
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize PostHog
posthog.api_key = os.getenv('POSTHOG_API_KEY')
posthog.host = os.getenv('POSTHOG_HOST', 'https://app.posthog.com')

# Capture test event
posthog.capture('test-id', 'test-event')