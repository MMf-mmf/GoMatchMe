# GoMatchMe

A comprehensive matchmaking platform built with Django, featuring real-time chat, payment processing, and intelligent matching algorithms.

## Features

- **User Authentication**: Secure user registration and login with email verification
- **Profile Management**: Comprehensive user profiles with customizable preferences
- **Intelligent Matching**: Advanced matching algorithms for connecting compatible users
- **Real-time Chat**: WebSocket-based messaging system for instant communication
- **Payment Processing**: Integrated Stripe payment system with multiple pricing tiers
- **Admin Dashboard**: Comprehensive admin interface for managing users and matches
- **Blog System**: Content management system for blog posts and articles
- **Responsive Design**: Mobile-first design with Tailwind CSS

## Tech Stack

- **Backend**: Django 4.1.5, Django REST Framework
- **Frontend**: React, Tailwind CSS, HTMX
- **Database**: PostgreSQL
- **Real-time**: Django Channels, WebSockets
- **Cache**: Redis
- **Task Queue**: Celery
- **Payment**: Stripe
- **Email**: Mailgun
- **Storage**: AWS S3
- **Deployment**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL
- Redis
- npm/yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gomatchme.git
   cd gomatchme
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements/local.txt
   ```

4. **Install Node.js dependencies**
   ```bash
   npm install
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Set up database**
   ```bash
   python manage.py migrate --settings=project.settings.local
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser --settings=project.settings.local
   ```

8. **Build frontend assets**
   ```bash
   npm run dev
   npm run tailwind-build
   ```

9. **Start Redis (required for real-time features)**
   ```bash
   redis-server
   # Or with Docker:
   docker run -it --rm --name redis -p 6379:6379 redis
   ```

10. **Start the development server**
    ```bash
    export DJANGO_SETTINGS_MODULE=project.settings.local
    python manage.py runserver
    ```

## Development Commands

### Django Commands
```bash
# Run development server
python manage.py runserver --settings=project.settings.local

# Run migrations
python manage.py migrate --settings=project.settings.local

# Create migrations
python manage.py makemigrations --settings=project.settings.local

# Collect static files
python manage.py collectstatic --settings=project.settings.local
```

### Frontend Commands
```bash
# Watch Tailwind CSS changes
npm run tailwind-watch

# Build Tailwind CSS for production
npm run tailwind-build

# Build React components
npm run dev
```

### Background Tasks
```bash
# Start Celery worker
celery -A project worker -l info

# Start Celery flower (monitoring)
celery -A project flower
```

## Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

### Required Settings
- `DJANGO_SECRET_KEY`: Django secret key
- `DEVELOPMENT_DATABASE_NAME`: Database name
- `DEVELOPMENT_DATABASE_USER`: Database user
- `DEVELOPMENT_DATABASE_PASSWORD`: Database password

### Third-party Services
- `STRIPE_SECRET_KEY_TEST`: Stripe test secret key
- `MAIL_GUN_API_KEY`: Mailgun API key
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `GOOGLE_MAPS_API_KEY`: Google Maps API key

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

## Testing

```bash
# Run tests
python manage.py test --settings=project.settings.local

# Run specific app tests
python manage.py test accounts_app --settings=project.settings.local
```

## Stripe Configuration

For payment processing, you'll need to:

1. Create a Stripe account
2. Set up the following products in your Stripe dashboard:
   - Bounty Payment (One Time)
   - Bounty Payment (Recurring)
   - Suggestion Payment
   - Donation Payment
   - Pledge Fulfillment (Match Made!)

3. For webhook testing in development:
   ```bash
   stripe listen --forward-to http://127.0.0.1:8000/payments/stripe_webhooks/
   ```

## Project Structure

```
├── accounts_app/          # User authentication and profiles
├── match_app/            # Matching algorithms and suggestions
├── chats_app/            # Real-time messaging
├── payments_app/         # Stripe payment processing
├── blog/                 # Blog and content management
├── templates/            # HTML templates
├── static/               # Static files (CSS, JS, images)
├── media/                # User uploaded files
├── project/              # Django project settings
└── requirements/         # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.
