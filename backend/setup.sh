#!/bin/bash

# Interior AI Backend Setup Script

set -e

echo "🚀 Interior AI Backend Setup"
echo "=============================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your credentials:"
    echo "   - REPLICATE_API_TOKEN"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo "   - S3_BUCKET_NAME"
    echo "   - SECRET_KEY (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')"
    echo ""
    read -p "Press Enter after you've updated .env..."
fi

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Docker detected. Would you like to use Docker? (recommended)"
    read -p "Use Docker? (y/n): " use_docker

    if [ "$use_docker" = "y" ] || [ "$use_docker" = "Y" ]; then
        echo ""
        echo "🐳 Starting services with Docker..."
        docker-compose up -d

        echo ""
        echo "⏳ Waiting for services to be ready..."
        sleep 10

        echo ""
        echo "📊 Running database migrations..."
        docker-compose exec -T api alembic upgrade head

        echo ""
        echo "✅ Setup complete!"
        echo ""
        echo "📚 Services running:"
        echo "   API: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo "   PostgreSQL: localhost:5432"
        echo "   Redis: localhost:6379"
        echo ""
        echo "📖 View logs with: docker-compose logs -f"
        echo "🛑 Stop services with: docker-compose down"
        exit 0
    fi
fi

# Manual setup
echo ""
echo "📦 Manual setup selected"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "⚠️  Make sure PostgreSQL and Redis are running:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
read -p "Press Enter when PostgreSQL and Redis are ready..."

# Run migrations
echo ""
echo "📊 Running database migrations..."
alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Start the API server with:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "🔄 Start the Celery worker with (in another terminal):"
echo "   source venv/bin/activate"
echo "   celery -A app.tasks.celery_app worker --loglevel=info"
echo ""
echo "📚 Access API docs at: http://localhost:8000/docs"
