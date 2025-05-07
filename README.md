# Planfix Dashboard with Claude AI Integration

A Django-based dashboard for Planfix project management system with Claude AI integration for data analysis and insights.

## Setup and Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd planfix-dashboard
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   `# Django settings
    SECRET_KEY=your_django_secret_key_here
    DEBUG=True
    ALLOWED_HOSTS=127.0.0.1,localhost
    
    # Planfix API settings
    PLANFIX_ACCOUNT_ID=deventky
    PLANFIX_API_TOKEN=
    
    
    # Claude API settings
    CLAUDE_API_KEY=
    CLAUDE_API_URL=https://api.anthropic.com/v1/messages
   ````

5. Run migrations and start the development server:
   ```
   python manage.py migrate
   python manage.py runserver
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
