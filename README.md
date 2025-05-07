Setup and Installation

Clone the repository:
git clone <repository-url>
cd planfix-dashboard

Create a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Create a .env file in the project root with the following variables:
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
PLANFIX_ACCOUNT=your-planfix-account
PLANFIX_API_TOKEN=your-planfix-token
ANTHROPIC_API_KEY=your-claude-api-key

Run migrations and start the development server:
python manage.py migrate
python manage.py runserver

Access the dashboard at http://127.0.0.1:8000/
