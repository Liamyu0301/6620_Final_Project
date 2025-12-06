# Auth Service

Handles user registration, login, and JWT token generation.

## Features

- **User Registration**: Create new user accounts
- **User Login**: Verify user credentials and return JWT token
- **JWT Generation**: Generate and verify JWT tokens

## API Endpoints

### POST /auth/register
Register a new user

Request body:
```json
{
  "username": "user123",
  "password": "password123",
  "email": "user@example.com"
}
```

Response:
```json
{
  "message": "Registration successful",
  "token": "eyJ...",
  "userId": "xxx",
  "username": "user123"
}
```

### POST /auth/login
User login

Request body:
```json
{
  "username": "user123",
  "password": "password123"
}
```

Response:
```json
{
  "message": "Login successful",
  "token": "eyJ...",
  "userId": "xxx",
  "username": "user123"
}
```

## Environment Variables

- `USERS_TABLE`: DynamoDB users table name
- `JWT_SECRET`: JWT signing secret

