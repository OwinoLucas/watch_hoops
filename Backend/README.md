# Watch Hoops API Documentation

## Overview

Watch Hoops is a basketball streaming platform API that provides access to live games, team information, player statistics, and news. This API uses JWT authentication and follows RESTful principles.

## Base URL

- Development: `http://localhost:8000/api`
- Production: `https://api.watchhoops.com`

## Authentication

All endpoints except registration and login require JWT authentication.

Include the token in request headers:
```
Authorization: Bearer <your_access_token>
```

### Authentication Endpoints

#### Register New User
```
POST /api/auth/register/
```
Request body:
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "VIEWER"  // VIEWER, PLAYER, ADMIN
}
```

#### Login
```
POST /api/auth/login/
```
Request body:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```
Response:
```json
{
  "access": "access_token",
  "refresh": "refresh_token"
}
```

#### Refresh Token
```
POST /api/auth/login/refresh/
```
Request body:
```json
{
  "refresh": "refresh_token"
}
```

#### Change Password
```
POST /api/auth/change-password/
```
Request body:
```json
{
  "old_password": "current_password",
  "new_password": "new_password"
}
```

## Teams and Leagues

### Leagues

#### List Leagues
```
GET /api/teams/leagues/
```
Query parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10)
- `ordering`: Sort field (e.g., name, -name)
- `search`: Search term

#### Get League Details
```
GET /api/teams/leagues/{id}/
```

#### Create League (Admin only)
```
POST /api/teams/leagues/
```
Request body:
```json
{
  "name": "NBA",
  "country": "US",
  "description": "National Basketball Association",
  "season_start": "2025-10-01",
  "season_end": "2026-06-30"
}
```

### Teams

#### List Teams
```
GET /api/teams/teams/
```
Query parameters:
- `league`: League ID
- `page`: Page number
- `page_size`: Items per page
- `ordering`: Sort field
- `search`: Search term

#### Get Team Details
```
GET /api/teams/teams/{id}/
```

#### Create Team (Admin only)
```
POST /api/teams/teams/
```
Request body:
```json
{
  "name": "Los Angeles Lakers",
  "league": 1,
  "home_venue": "Crypto.com Arena",
  "description": "Team description",
  "founded_year": 1947,
  "team_colors": "Purple and Gold"
}
```

## Players

#### List Players
```
GET /api/players/players/
```
Query parameters:
- `team`: Team ID
- `position`: Player position (PG, SG, SF, PF, C)
- `active`: Active status (true/false)
- `nationality`: Country code

#### Get Player Details
```
GET /api/players/players/{id}/
```

#### Create Player (Admin only)
```
POST /api/players/players/
```
Request body:
```json
{
  "user": {
    "email": "player@example.com",
    "password": "password",
    "first_name": "LeBron",
    "last_name": "James",
    "user_type": "PLAYER"
  },
  "team": 1,
  "position": "SF",
  "jersey_number": 23,
  "height_cm": 206,
  "weight_kg": 113,
  "nationality": "US",
  "date_of_birth": "1984-12-30"
}
```

### Player Statistics

#### Get Player Statistics
```
GET /api/players/stats/
```
Query parameters:
- `player`: Player ID
- `game`: Game ID
- `date_from`: Start date
- `date_to`: End date

## Games

#### List Games
```
GET /api/games/matches/
```
Query parameters:
- `status`: Game status (SCHEDULED, LIVE, FINISHED, POSTPONED)
- `team`: Team ID
- `league`: League ID
- `date_from`: Start date
- `date_to`: End date

#### Get Game Details
```
GET /api/games/matches/{id}/
```

#### Create Game (Admin only)
```
POST /api/games/matches/
```
Request body:
```json
{
  "home_team": 1,
  "away_team": 2,
  "league": 1,
  "date_time": "2025-05-01T19:30:00Z",
  "venue": "Crypto.com Arena",
  "ticket_price": 50.00,
  "streaming_price": 9.99,
  "available_tickets": 20000
}
```

### Game Statistics

#### Get Game Statistics
```
GET /api/games/match-stats/{game_id}/
```

## News

#### List Articles
```
GET /api/news/articles/
```
Query parameters:
- `category`: Category ID
- `tag`: Tag ID
- `featured`: Featured status (true/false)
- `author`: Author ID
- `ordering`: Sort field (-published_date, title)

#### Get Article Details
```
GET /api/news/articles/{id}/
```

#### Create Article (Admin only)
```
POST /api/news/articles/
```
Request body (multipart/form-data):
```
title: "Article Title"
content: "Article content"
featured_image: [file upload]
categories: [1, 2]
tags: [1, 2]
is_featured: false
meta_description: "SEO description"
meta_keywords: "keyword1, keyword2"
```

## Streaming

#### List Available Streams
```
GET /api/streaming/streams/
```
Query parameters:
- `status`: Stream status (SCHEDULED, LIVE, ENDED)
- `game`: Game ID
- `quality`: Stream quality (SD, HD, FHD, UHD)

#### Purchase Stream Access
```
POST /api/streaming/access/purchase/
```
Request body:
```json
{
  "stream_id": 1,
  "plan_id": 1,
  "quality": "HD"
}
```

#### Start Viewing Session
```
POST /api/streaming/sessions/start/
```
Request body:
```json
{
  "stream_id": 1,
  "quality": "HD",
  "device_type": "desktop"
}
```

## Error Responses

All error responses follow this format:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

Common error codes:
- `AUTH_REQUIRED`: Authentication required
- `INVALID_CREDENTIALS`: Invalid login credentials
- `PERMISSION_DENIED`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid input data
- `RATE_LIMIT_EXCEEDED`: Too many requests

## Pagination

List endpoints return paginated results:
```json
{
  "count": 100,
  "next": "http://api.example.com/items/?page=2",
  "previous": null,
  "results": []
}
```

## Rate Limiting

- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- Admin: 5000 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1618566789
```

## Relationships

### Core Relationships:
1. Teams belong to Leagues
2. Players belong to Teams
3. Games involve two Teams (home and away)
4. Articles can reference Teams, Players, and Games
5. Streams are associated with Games

### User Types and Access:
1. Viewers:
   - Can view all public data
   - Can purchase stream access
   - Can view purchased streams

2. Players:
   - Have player profiles
   - Can view team-specific data
   - Can view personal statistics

3. Admins:
   - Full access to all endpoints
   - Can manage all resources
   - Can create and modify content

## Best Practices

1. Always include authentication token for protected endpoints
2. Use pagination for list endpoints
3. Include error handling for all requests
4. Monitor rate limits
5. Use appropriate HTTP methods:
   - GET for retrieving data
   - POST for creating resources
   - PUT for updating resources
   - DELETE for removing resources

## Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```
6. Run development server:
   ```bash
   python manage.py runserver
   ```

## Testing

Refer to [API_TESTING.txt](API_TESTING.txt) for detailed testing instructions using Postman or Insomnia.

## Support

For API support, contact:
- Email: api@watchhoops.com
- Documentation: https://docs.watchhoops.com
- Issue Tracker: https://github.com/watchhoops/api/issues

