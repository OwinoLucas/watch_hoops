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
```
GET /api/games/match-stats/{game_id}/
```

## Analytics

The Analytics API provides access to advanced basketball analytics, insights, and predictions for players, teams, and games.

### Player Analytics

#### List Player Analytics
```
GET /api/analytics/player-analytics/
```
Query parameters:
- `player`: Player ID
- `team`: Team ID
- `date_from`: Start date
- `date_to`: End date
- `trend_direction`: Filter by trend (IMPROVING, DECLINING, STABLE)

Response:
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "player": 23,
      "date": "2025-04-15",
      "points_avg": 28.5,
      "rebounds_avg": 7.2,
      "assists_avg": 6.8,
      "efficiency_rating": 24.3,
      "field_goal_percentage": 48.2,
      "three_point_percentage": 36.5,
      "free_throw_percentage": 82.0,
      "steals_avg": 1.2,
      "blocks_avg": 0.8,
      "turnovers_avg": 2.3,
      "minutes_avg": 34.5,
      "last_10_games_rating": 25.8,
      "trend_direction": "IMPROVING"
    }
  ]
}
```

#### Get Player Shooting Statistics
```
GET /api/analytics/player-analytics/{id}/shooting-stats/
```

Response:
```json
{
  "field_goal_percentage": 48.2,
  "three_point_percentage": 36.5,
  "free_throw_percentage": 82.0,
  "true_shooting_percentage": 58.7,
  "player_id": 23,
  "player_name": "LeBron James",
  "date": "2025-04-15"
}
```
```

#### Get Player Efficiency Leaders
```
GET /api/analytics/player-analytics/efficiency-leaders/
```

Query parameters:
- `count`: Number of leaders to return (default: 10)
- `team`: Filter by team ID

Response:
```json
[
  {
    "id": 15,
    "player": 23,
    "date": "2025-04-15",
    "points_avg": 28.5,
    "rebounds_avg": 7.2,
    "assists_avg": 6.8,
    "efficiency_rating": 30.2,
    "field_goal_percentage": 52.6,
    "trend_direction": "IMPROVING"
  },
  {
    "id": 8,
    "player": 15,
    "date": "2025-04-15",
    "points_avg": 25.3,
    "rebounds_avg": 11.5,
    "assists_avg": 3.2,
    "efficiency_rating": 28.7,
    "field_goal_percentage": 49.2,
    "trend_direction": "STABLE"
  }
]
```

#### Get Player Trend Analysis
```
GET /api/analytics/player-analytics/{id}/trend/
```

Query parameters:
- `days`: Number of days to analyze (default: 30)

Response:
```json
{
  "player_id": 23,
  "player_name": "LeBron James",
  "trend_direction": "IMPROVING",
  "current_rating": 27.5,
  "previous_rating": 24.8,
  "days_analyzed": 30,
  "shooting_trend": {
    "current_fg": 48.2,
    "previous_fg": 46.5,
    "current_3pt": 38.6,
    "previous_3pt": 36.2
  }
}
```

#### Get Hot/Cold Streaks
```
GET /api/analytics/player-analytics/streaks/
```

Query parameters:
- `type`: Streak type (hot or cold, default: hot)
- `team`: Filter by team ID

Response:
```json
[
  {
    "id": 23,
    "player": 15,
    "date": "2025-04-15",
    "points_avg": 32.5,
    "efficiency_rating": 29.3,
    "last_10_games_rating": 31.2,
    "trend_direction": "IMPROVING"
  }
]
```

### Team Analytics

#### List Team Analytics
```
GET /api/analytics/team-analytics/
```

Query parameters:
- `team`: Team ID
- `league`: League ID
- `date_from`: Start date
- `date_to`: End date

Response:
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "team": 1,
      "date": "2025-04-15",
      "wins": 45,
      "losses": 28,
      "points_scored_avg": 113.5,
      "points_allowed_avg": 105.8,
      "win_percentage": 61.6
    }
  ]
}
```

#### Get Team Performance Trends
```
GET /api/analytics/team-performance-trends/
```

Query parameters:
- `team`: Team ID (required)
- `period_type`: Period type (WEEK, MONTH, SEASON)
- `date_from`: Start date
- `date_to`: End date

Response:
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "team": 1,
      "period_start": "2025-03-15",
      "period_end": "2025-04-15",
      "period_type": "MONTH",
      "games_played": 16,
      "wins": 11,
      "losses": 5,
      "points_scored_avg": 112.3,
      "points_allowed_avg": 106.5,
      "streak_type": "WIN",
      "streak_count": 4,
      "trend_direction": "IMPROVING",
      "offensive_efficiency": 113.8,
      "defensive_efficiency": 107.2,
      "pace": 98.5
    }
  ]
}
```

#### Get Quarter-by-Quarter Analysis
```
GET /api/analytics/team-performance-trends/{id}/quarter-analysis/
```

Response:
```json
{
  "team_id": 1,
  "team_name": "Los Angeles Lakers",
  "period": "2025-03-15 to 2025-04-15",
  "quarters": {
    "q1": {
      "points_scored": 27.5,
      "points_allowed": 25.8,
      "net_rating": 1.7
    },
    "q2": {
      "points_scored": 28.2,
      "points_allowed": 26.3,
      "net_rating": 1.9
    },
    "q3": {
      "points_scored": 26.8,
      "points_allowed": 27.5,
      "net_rating": -0.7
    },
    "q4": {
      "points_scored": 29.8,
      "points_allowed": 26.9,
      "net_rating": 2.9
    }
  },
  "strongest_quarter": "q4",
  "weakest_quarter": "q3"
}
```

#### Get Home/Away Splits
```
GET /api/analytics/team-performance-trends/{id}/home-away-splits/
```

Response:
```json
{
  "team_id": 1,
  "team_name": "Los Angeles Lakers",
  "period": "2025-03-15 to 2025-04-15",
  "home": {
    "games": 8,
    "wins": 6,
    "losses": 2,
    "win_percentage": 75.0,
    "points_scored_avg": 115.8,
    "points_allowed_avg": 105.3,
    "point_differential": 10.5
  },
  "away": {
    "games": 8,
    "wins": 5,
    "losses": 3,
    "win_percentage": 62.5,
    "points_scored_avg": 108.8,
    "points_allowed_avg": 107.7,
    "point_differential": 1.1
  },
  "home_vs_away_differential": {
    "win_percentage": 12.5,
    "points_scored": 7.0,
    "points_allowed": -2.4
  }
}
```

### Game Predictions

#### List Game Predictions
```
GET /api/analytics/game-predictions/
```

Query parameters:
- `game`: Game ID

Response:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "game": 42,
      "home_team_win_probability": 65.2,
      "predicted_home_score": 110,
      "predicted_away_score": 102,
      "home_q1_score": 27,
      "home_q2_score": 28,
      "home_q3_score": 26,
      "home_q4_score": 29,
      "away_q1_score": 25,
      "away_q2_score": 26,
      "away_q3_score": 27,
      "away_q4_score": 24,
      "key_matchup_factors": {
        "key_player_matchups": [
          {
            "home_player": {
              "id": 23,
              "name": "LeBron James",
              "position": "SF",
              "efficiency": 27.5
            },
            "away_player": {
              "id": 15,
              "name": "Kevin Durant",
              "position": "SF",
              "efficiency": 26.8
            },
            "advantage": "slight_home",
            "impact_level": "high"
          }
        ],
        "home_advantage": "strong",
        "predicted_pace": "moderate"
      },
      "created_at": "2025-04-15T10:30:00Z"
    }
  ]
}
```

#### List Player Performance Predictions
```
GET /api/analytics/player-predictions/
```

Query parameters:
- `player`: Player ID
- `game`: Game ID
- `team`: Team ID
- `min_confidence`: Minimum confidence score (0-100)

Response:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "player": 23,
      "game": 42,
      "predicted_points": 28,
      "predicted_rebounds": 7,
      "predicted_assists": 8,
      "predicted_steals": 1,
      "predicted_blocks": 1,
      "predicted_minutes": 36,
      "predicted_efficiency": 32.5,
      "confidence_score": 85.0,
      "factors": {
        "recent_form": "good",
        "matchup_history": "favorable",
        "minutes_projection": "high"
      },
      "created_at": "2025-04-15T10:30:00Z"
    }
  ]
}
```

#### Generate Predictions (Admin only)
```
POST /api/analytics/player-predictions/generate/
```

Request body:
```json
{
  "game": 42
}
```

Response:
```json
{
  "predictions_created": 12,
  "games_processed": 1,
  "players_processed": 12
}
```

### Real-Time Analytics

#### Get Live Game Statistics
```
GET /api/analytics/real-time/live-game-stats/{game_id}/
```

Response:
```json
{
  "game_id": 42,
  "game_status": "LIVE",
  "current_quarter": 3,
  "time_remaining": "08:24",
  "home_score": 65,
  "away_score": 62,
  "home_team": "Los Angeles Lakers",
  "away_team": "Brooklyn Nets",
  "player_stats": [
    {
      "player_id": 23,
      "player_name": "LeBron James",
      "team": "Los Angeles Lakers",
      "points": 18,
      "rebounds": 5,
      "assists": 6,
      "steals": 1,
      "blocks": 0,
      "field_goals": "7-12",
      "three_pointers": "2-5",
      "free_throws": "2-2",
      "plus_minus": 8
    }
  ],
  "quarter_scores": {
    "home": [24, 28, 13, 0],
    "away": [22, 23, 17, 0]
  },
  "last_5_plays": [
    {
      "time": "08:42",
      "description": "LeBron James makes 20-foot jump shot (A. Davis assists)",
      "team": "Los Angeles Lakers",
      "score_change": 2
    }
  ]
}
```

#### Get Live Player Statistics
```
GET /api/analytics/real-time/player-stats/{player_id}/
```

Response:
```json
{
  "player_id": 23,
  "player_name": "LeBron James",
  "current_game": {
    "game_id": 42,
    "points": 18,
    "rebounds": 5,
    "assists": 6,
    "steals": 1,
    "blocks": 0,
    "minutes_played": 24,
    "efficiency": 22.5,
    "plus_minus": 8
  },
  "season_averages": {
    "points": 27.8,
    "rebounds": 7.3,
    "assists": 7.5,
    "efficiency": 30.2
  },
  "comparison_to_average": {
    "points": -9.8,
    "rebounds": -2.3,
    "assists": -1.5,
    "efficiency": -7.7
  }
}
```

#### Get Trending Players
```
GET /api/analytics/real-time/trending-players/
```

Query parameters:
- `limit`: Number of players to return (default: 5)
- `trend`: Type of trend (improving, declining, all)

Response:
```json
[
  {
    "player_id": 23,
    "player_name": "LeBron James",
    "team": "Los Angeles Lakers",
    "trend_direction": "IMPROVING",
    "current_rating": 32.5,
    "last_5_games_rating": 35.8,
    "last_game_stats": {
      "points": 32,
      "rebounds": 8,
      "assists": 9,
      "efficiency": 38.5
    }
  },
  {
    "player_id": 15,
    "player_name": "Kevin Durant",
    "team": "Brooklyn Nets",
    "trend_direction": "IMPROVING",
    "current_rating": 31.2,
    "last_5_games_rating": 33.6,
    "last_game_stats": {
      "points": 35,
      "rebounds": 6,
      "assists": 4,
      "efficiency": 36.8
    }
  }
]
```

#### Process Real-Time Game Data (Admin only)
```
POST /api/analytics/real-time/process-data/
```

Request body:
```json
{
  "game_id": 42,
  "home_score": 82,
  "away_score": 76,
  "status": "LIVE",
  "player_stats": [
    {
      "player_id": 23,
      "points": 20,
      "rebounds": 5,
      "assists": 4,
      "field_goals_made": 8,
      "field_goals_attempted": 15
    }
  ]
}
```

Response:
```json
{
  "status": "success",
  "message": "Processed real-time data for game 42",
  "updated_stats": 1
}
```

#### WebSocket Connection for Real-Time Updates

Connect to WebSocket endpoint:
```
ws://api.watchhoops.com/ws/analytics/game/{game_id}/
```

Authentication:
Include JWT token in the connection query parameters:
```
ws://api.watchhoops.com/ws/analytics/game/42/?token=your_jwt_token
```

Message format (received):
```json
{
  "type": "game_update",
  "data": {
    "game_id": 42,
    "home_score": 85,
    "away_score": 78,
    "time_remaining": "06:42",
    "quarter": 3,
    "last_play": {
      "player_id": 23,
      "action": "made 3-pointer",
      "time": "06:53"
    }
  }
}
```

## Reports

The Reports API provides access to detailed performance and financial reports with various filtering, aggregation, and export options.

### Revenue Reports

#### Get Revenue Summary
```
GET /api/reports/revenue/summary/
```

Query parameters:
- `period`: Time period (week, month, quarter, year, all)
- `start_date`: Custom period start date
- `end_date`: Custom period end date
- `source`: Revenue source (tickets, streaming, merchandise, all)

Response:
```json
{
  "period": "month",
  "start_date": "2025-03-15",
  "end_date": "2025-04-15",
  "total_revenue": 1285350.75,
  "by_source": {
    "tickets": 875250.00,
    "streaming": 358750.50,
    "merchandise": 51350.25
  },
  "by_team": [
    {
      "team_id": 1,
      "team_name": "Los Angeles Lakers",
      "revenue": 287500.50
    },
    {
      "team_id": 2,
      "team_name": "Golden State Warriors",
      "revenue": 265750.25
    }
  ],
  "comparison_to_previous": {
    "percentage_change": 12.5,
    "absolute_change": 142650.25
  }
}
```

#### Get Revenue Details
```
GET /api/reports/revenue/details/
```

Query parameters:
- `period`: Time period (daily, weekly, monthly, quarterly)
- `start_date`: Start date
- `end_date`: End date
- `source`: Revenue source
- `team`: Team ID
- `group_by`: Grouping (date, team, source)

Response:
```json
{
  "total_items": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "date": "2025-04-01",
      "tickets": {
        "revenue": 98500.00,
        "transactions": 1835,
        "avg_price": 53.68
      },
      "streaming": {
        "revenue": 35250.75,
        "transactions": 3580,
        "avg_price": 9.85
      },
      "merchandise": {
        "revenue": 5280.50,
        "transactions": 145,
        "avg_price": 36.42
      },
      "total": 139031.25
    }
  ]
}
```

#### Get Quarterly Aggregation
```
GET /api/reports/revenue/quarterly/
```

Query parameters:
- `year`: Year to analyze (default: current year)
- `team`: Team ID

Response:
```json
{
  "year": 2025,
  "quarters": [
    {
      "quarter": "Q1",
      "revenue": 3568250.75,
      "top_game": {
        "game_id": 125,
        "teams": "Lakers vs. Warriors",
        "revenue": 285000.00,
        "date": "2025-03-25"
      },
      "by_source": {
        "tickets": 2458250.00,
        "streaming": 982500.50,
        "merchandise": 127500.25
      }
    },
    {
      "quarter": "Q2",
      "revenue": 2985250.50,
      "top_game": {
        "game_id": 225,
        "teams": "Bucks vs. Nets",
        "revenue": 245000.00,
        "date": "2025-04-12"
      },
      "by_source": {
        "tickets": 2058250.00,
        "streaming": 812500.50,
        "merchandise": 114500.00
      }
    }
  ],
  "yearly_total": 6553501.25,
  "yearly_forecast": 12850000.00
}
```

#### Export Revenue Report (CSV/PDF)
```
GET /api/reports/revenue/export/
```

Query parameters:
- `format`: Export format (csv, pdf)
- `period`: Time period
- `start_date`: Start date
- `end_date`: End date
- `source`: Revenue source
- `team`: Team ID
- `include_charts`: Include charts in PDF (true/false)

Response:
File download with appropriate Content-Type header

### Performance Reports

#### Get Player Performance Report
```
GET /api/reports/performance/player/
```

Query parameters:
- `player`: Player ID (required)
- `period`: Time period (week, month, season, all)
- `start_date`: Custom period start date
- `end_date`: Custom period end date
- `metrics`: Comma-separated list of metrics to include

Response:
```json
{
  "player_id": 23,
  "player_name": "LeBron James",
  "team": "Los Angeles Lakers",
  "period": "month",
  "start_date": "2025-03-15",
  "end_date": "2025-04-15",
  "games_played": 12,
  "minutes_per_game": 35.8,
  "performance": {
    "points": {
      "total": 336,
      "average": 28.0,
      "high": 38,
      "low": 18
    },
    "rebounds": {
      "total": 86,
      "average": 7.2,
      "high": 12,
      "low": 4
    },
    "assists": {
      "total": 92,
      "average": 7.7,
      "high": 15,
      "low": 3
    },
    "efficiency": {
      "total": 379.2,
      "average": 31.6,
      "high": 42.5,
      "low": 21.3
    }
  },
  "shooting": {
    "field_goals": {
      "made": 121,
      "attempted": 248,
      "percentage": 48.8
    },
    "three_pointers": {
      "made": 28,
      "attempted": 76,
      "percentage": 36.8
    },
    "free_throws": {
      "made": 66,
      "attempted": 83,
      "percentage": 79.5
    }
  },
  "advanced": {
    "true_shooting": 58.7,
    "plus_minus": 125,
    "per_36_minutes": {
      "points": 28.2,
      "rebounds": 7.3,
      "assists": 7.7
    }
  },
  "trend": {
    "direction": "IMPROVING",
    "last_5_games_avg": 31.2,
    "comparison_to_season": "+2.5"
  }
}
```

#### Get Team Performance Report
```
GET /api/reports/performance/team/
```

Query parameters:
- `team`: Team ID (required)
- `period`: Time period
- `start_date`: Custom period start date
- `end_date`: Custom period end date
- `include_players`: Include player breakdowns (true/false)

Response:
```json
{
  "team_id": 1,
  "team_name": "Los Angeles Lakers",
  "period": "month",
  "start_date": "2025-03-15",
  "end_date": "2025-04-15",
  "record": {
    "games": 15,
    "wins": 10,
    "losses": 5,
    "win_percentage": 66.7,
    "home_record": "6-2",
    "away_record": "4-3"

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

## Search

The Search API allows you to search across multiple content types including players, teams, games, and news articles. It uses Elasticsearch for fast and relevant search results with features like fuzzy matching and filtering.

### Global Search

#### Search Across All Content Types
```
GET /api/search/global/
```
Query parameters:
- `q`: Search query (required, minimum 3 characters)
- `limit`: Number of results per content type (default: 5)
- `type`: Filter by content type(s) (comma-separated: player,team,game,article)

Response:
```json
{
  "count": 12,
  "results": [
    {
      "id": 23,
      "name": "LeBron James",
      "position": "SF",
      "jersey_number": 23,
      "team_name": "Los Angeles Lakers",
      "object_type": "player"
    },
    {
      "id": 1,
      "name": "Los Angeles Lakers",
      "home_venue": "Crypto.com Arena",
      "founded_year": 1947,
      "league_name": "NBA",
      "object_type": "team"
    },
    {
      "id": 42,
      "date_time": "2025-05-01T19:30:00Z",
      "venue": "Crypto.com Arena",
      "status": "SCHEDULED",
      "home_team_name": "Los Angeles Lakers",
      "away_team_name": "Brooklyn Nets",
      "object_type": "game"
    },
    {
      "id": 15,
      "title": "Lakers clinch playoff spot with win over Nets",
      "published_date": "2025-04-12T08:30:00Z",
      "author_name": "John Smith",
      "categories": ["NBA", "Lakers", "Playoffs"],
      "is_featured": true,
      "object_type": "article"
    }
  ]
}
```

### Type-Specific Search

#### Search Players
```
GET /api/search/players/
```
Query parameters:
- `q`: Search query (required, minimum 2 characters)
- `position`: Filter by player position (PG, SG, SF, PF, C)
- `team`: Filter by team ID
- `limit`: Number of results (default: 20)

#### Search Teams
```
GET /api/search/teams/
```
Query parameters:
- `q`: Search query (required, minimum 2 characters)
- `league`: Filter by league ID
- `limit`: Number of results (default: 20)

#### Search Games
```
GET /api/search/games/
```
Query parameters:
- `q`: Search query (required, minimum 2 characters)
- `status`: Filter by game status (SCHEDULED, LIVE, FINISHED, POSTPONED)
- `team`: Filter by team ID (matches either home or away team)
- `limit`: Number of results (default: 20)

#### Search Articles
```
GET /api/search/articles/
```
Query parameters:
- `q`: Search query (required, minimum 2 characters)
- `featured`: Filter by featured status (true/false)
- `category`: Filter by category ID
- `limit`: Number of results (default: 20)

### Search Suggestions

#### Get Search Suggestions
```
GET /api/search/suggestions/
```
Query parameters:
- `q`: Partial search query

Response:
```json
[
  "Lakers",
  "LeBron James",
  "LA Clippers",
  "Larry Bird",
  "Lakers vs Nets"
]
```

## Caching

Watch Hoops uses Redis for caching to improve performance and reduce database load. The caching system is configured with multiple cache backends for different use cases.

### Cache Configuration

#### Default Cache
```python
# Default cache for general purpose use
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'watchhoops',
        'TIMEOUT': 60 * 60 * 24,  # 24 hours default timeout
    }
}
```

#### Session Cache
```python
# Session cache for storing user sessions
CACHES = {
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'watchhoops_session',
    }
}
```

#### Analytics Cache
```python
# Analytics cache for storing frequently accessed analytics data
CACHES = {
    'analytics': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/3',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'watchhoops_analytics',
        'TIMEOUT': 60 * 60 * 2,  # 2 hours for analytics data
    }
}
```

### Cache Usage Examples

#### Caching API Responses
```python
from django.core.cache import cache

def get_player_stats(player_id):
    # Cache key with appropriate prefix
    cache_key = f"player_stats:{player_id}"
    
    # Try to get data from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch data from database if not in cache
    player_stats = PlayerStats.objects.filter(player_id=player_id)
    data = serialize_player_stats(player_stats)
    
    # Cache the data (timeout in seconds)
    cache.set(cache_key, data, timeout=60*60)  # 1 hour
    
    return data
```

#### Using the Cache Decorator
```python
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class TeamStatsView(APIView):
    @method_decorator(cache_page(60*30))  # Cache for 30 minutes
    def get(self, request, team_id):
        # This response will be cached
        stats = TeamStats.objects.get(team_id=team_id)
        serializer = TeamStatsSerializer(stats)
        return Response(serializer.data)
```

#### Cache Invalidation
```python
from django.core.cache import cache

def update_player_stats(player_id, new_stats):
    # Update the database
    player_stats = PlayerStats.objects.get(player_id=player_id)
    player_stats.update(**new_stats)
    
    # Invalidate cache
    cache_key = f"player_stats:{player_id}"
    cache.delete(cache_key)
    
    # Optional: also invalidate related caches
    cache.delete(f"team_stats:{player_stats.team_id}")
```

## Monitoring and Health Checks

Watch Hoops includes a comprehensive monitoring system for tracking API performance, system health, and detecting issues.

### Health Check Endpoints

#### Basic Health Check
```
GET /api/monitoring/health/basic/
```
This endpoint is public and returns a simple status indicating if the API is running.

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-04-16T10:30:00Z",
  "api_version": "1.0.0"
}
```

#### Detailed Health Check
```
GET /api/monitoring/health/detailed/
```
This endpoint requires authentication and provides detailed health information about all system components.

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-04-16T10:30:00Z",
  "api_version": "1.0.0",
  "components": {
    "api": {
      "status": "healthy",
      "uptime": 86400
    },
    "database": {
      "status": "healthy",
      "message": "Connection OK"
    },
    "cache": {
      "status": "healthy",
      "message": "Connection OK"
    },
    "elasticsearch": {
      "status": "healthy",
      "message": "Connection OK"
    }
  },
  "system": {
    "memory": {
      "total": 8589934592,
      "available": 4294967296,
      "used_percent": 50.0
    },
    "disk": {
      "total": 107374182400,
      "free": 53687091200,
      "used_percent": 50.0
    },
    "cpu": {
      "usage_percent": 25.0,
      "count": 4
    }
  }
}
```

### Performance Metrics

#### API Performance Metrics
```
GET /api/monitoring/metrics/performance/
```
This endpoint requires admin privileges and provides API performance metrics.

Query parameters:
- `days`: Number of days of data to include (default: 7)

Response:
```json
{
  "time_series": [
    {
      "date": "2025-04-16",
      "requests": 12500,
      "avg_response_time": 125,
      "errors": 25,
      "response_time_avg": 125,
      "response_time_max": 750,
      "response_time_min": 15
    },
    {
      "date": "2025-04-15",
      "requests": 11800,
      "avg_response_time": 120,
      "errors": 20,
      "response_time_avg": 120,
      "response_time_max": 680,
      "response_time_min": 18
    }
  ],
  "status_codes": [
    {
      "status_code": 200,
      "count": 23500
    },
    {
      "status_code": 404,
      "count": 520
    },
    {
      "status_code": 500,
      "count": 45
    }
  ],
  "summary": {
    "total_requests": 24300,
    "total_errors": 45,
    "avg_response_time": 122.5,
    "error_rate": 0.2
  }
}
```

#### System Resource Metrics
```
GET /api/monitoring/metrics/system/
```
This endpoint requires admin privileges and provides system resource usage metrics.

Query parameters:
- `days`: Number of days of data to include (default: 7)

Response:
```json
{
  "time_series": [
    {
      "date": "2025-04-16",
      "cpu_avg": 30.5,
      "cpu_max": 85.2,
      "cpu_min": 10.1,
      "memory_avg": 62.3,
      "memory_max": 78.9,
      "memory_min": 45.2
    }
  ],
  "current": {
    "cpu": {
      "usage_percent": 35.2,
      "count": 4
    },
    "memory": {
      "total": 8589934592,
      "available": 3221225472,
      "used_percent": 62.5
    },
    "disk": {
      "total": 107374182400,
      "free": 42949672960,
      "used_percent": 60.0
    }
  }
}
```

### Request and Error Logs

#### View Request Logs
```
GET /api/monitoring/logs/requests/
```
This endpoint requires admin privileges and provides access to API request logs.

Query parameters:
- `path`: Filter by request path
- `method`: Filter by HTTP method
- `status_code`: Filter by status code
- `user`: Filter by user ID
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `limit`: Number of logs to return (default: 100)

Response:
```json
{
  "count": 100,
  "logs": [
    {
      "id": 12345,
      "path": "/api/games/matches/42/",
      "method": "GET",
      "status_code": 200,
      "response_time_ms": 45,
      "user_id": 123,
      "ip_address": "192.168.1.1",
      "created_at": "2025-04-16T10:15:30Z"
    }
  ]
}
```

#### View Error Logs
```
GET /api/monitoring/logs/errors/
```
This endpoint requires admin privileges and provides access to API error logs.

Query parameters:
- `path`: Filter by request path
- `error_type`: Filter by error type
- `user`: Filter by user ID
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `limit`: Number of logs to return (default: 100)

Response:
```json
{
  "count": 10,
  "logs": [
    {
      "id": 456,
      "path": "/api/games/matches/999/",
      "method": "GET",
      "error_type": "DoesNotExist",
      "error_message": "Game matching query does not exist.",
      "user_id": 123,
      "ip_address": "192.168.1.1",
      "created_at": "2025-04-16T09:45:12Z"
    }
  ]
}
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

