# Watch Hoops Project

Watch Hoops is a basketball streaming platform that allows users to watch live games, follow their favorite teams and players, and stay updated with the latest basketball news.

## Project Structure

```
watch_hoops/
├── Backend/          # Django REST API backend
├── frontend/         # React frontend application
└── docker/          # Docker configuration files
```

## Prerequisites

- Python 3.12 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Redis 6 or higher
- ffmpeg (for video streaming)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/watch_hoops.git
cd watch_hoops
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r Backend/requirements.txt
```

### 3. Set Up Database

```bash
# Create PostgreSQL database
psql -U postgres
CREATE DATABASE watch_hoops;
CREATE USER watch_hoops_user WITH PASSWORD '\''your_password\'';
GRANT ALL PRIVILEGES ON DATABASE watch_hoops TO watch_hoops_user;
\q
```

### 4. Configure Environment Variables

```bash
# Copy example environment files
cp Backend/.env.example Backend/.env
cp frontend/.env.example frontend/.env

# Edit the .env files with your configuration
# Backend/.env
nano Backend/.env
```

Required environment variables:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://watch_hoops_user:your_password@localhost:5432/watch_hoops
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### 5. Initialize Backend

```bash
cd Backend

# Apply database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (if available)
python manage.py loaddata initial_data.json

# Start Django development server
python manage.py runserver
```

### 6. Set Up Frontend

```bash
cd ../frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

### 7. Setup Redis

```bash
# Install Redis (if not already installed)
# On Ubuntu/Debian:
sudo apt-get install redis-server

# On macOS:
brew install redis

# On Windows:
# Download and install from https://redis.io/download

# Start Redis server
# On Unix-based systems:
redis-server

# On Windows:
redis-server.exe
```

### 8. Setup Media Storage

```bash
# Create media directory
mkdir -p Backend/media/uploads
```

## Running Tests

### Backend Tests
```bash
cd Backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Development Tools

### Backend Development

1. Django Admin Interface:
   - Access at: http://localhost:8000/admin/
   - Use superuser credentials

2. API Documentation:
   - Access at: http://localhost:8000/api/docs/
   - Detailed API documentation in Backend/README.md

3. Debug Toolbar:
   - Automatically enabled in development
   - View SQL queries, cache operations, etc.

### Frontend Development

1. Development Server:
   - Access at: http://localhost:3000
   - Hot reloading enabled

2. Component Storybook:
   ```bash
   cd frontend
   npm run storybook
   ```

3. Code Quality Tools:
   ```bash
   # Run ESLint
   npm run lint

   # Run Prettier
   npm run format
   ```

## Common Issues and Solutions

### Backend Issues

1. Database Migrations:
   ```bash
   # Reset migrations
   python manage.py migrate --fake zero
   python manage.py migrate
   ```

2. Dependencies Issues:
   ```bash
   # Update dependencies
   pip install -r requirements.txt --upgrade
   ```

3. Media Files Not Loading:
   - Check media directory permissions
   - Verify MEDIA_URL and MEDIA_ROOT settings

### Frontend Issues

1. Node Modules Issues:
   ```bash
   # Clear node_modules and reinstall
   rm -rf node_modules
   npm install
   ```

2. Build Issues:
   ```bash
   # Clear cache and rebuild
   npm run clean
   npm run build
   ```

## Deployment

Refer to `docker/README.md` for production deployment instructions using Docker.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact: support@watchhoops.com

