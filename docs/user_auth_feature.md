# User Authentication and File Download Feature

## New Features

### 1. User Registration and Login
- **Registration**: Users can create new accounts (username, password, optional email)
- **Login**: Users can login with username and password
- **JWT Authentication**: Uses JWT tokens for authentication, tokens expire after 7 days

### 2. User Data Isolation
- **File Upload**: All uploaded files are associated with the currently logged-in user
- **File Search**: Users can only search and view their own uploaded files
- **Status Query**: Users can only view the status of their own files

### 3. File Download Feature
- **Secure Download**: Users can only download their own uploaded files
- **Presigned URL**: Uses S3 presigned URLs with 15-minute expiration
- **Frontend Integration**: Direct download button in search results

## New Services

### 1. Auth Service (`services/auth_service/`)
- **Endpoints**: 
  - `POST /auth/register` - User registration
  - `POST /auth/login` - User login
- **Features**: User registration, login, JWT token generation

### 2. Download Service (`services/download_service/`)
- **Endpoint**: `GET /download?documentId={id}`
- **Features**: Verify user identity and document ownership, generate S3 presigned download URLs

## Database Changes

### New Table
- **UsersTable**: Stores user information
  - Primary Key: `username`
  - Fields: `userId`, `email`, `passwordHash`, `createdAt`

### Existing Table Changes
- **DocumentsTable**: Added `userId` field to associate documents with users

## API Changes

All endpoints that require authentication now need to include in the request header:
```
Authorization: Bearer {token}
```

### Protected Endpoints
- `POST /documents` - Upload document
- `GET /search` - Search documents
- `GET /status/{id}` - Check status
- `GET /download?documentId={id}` - Download file

### Public Endpoints
- `POST /auth/register` - Register
- `POST /auth/login` - Login

## Frontend Changes

### New UI
- **Login/Register Tab**: Users need to login or register on first visit
- **User Info Display**: Shows username and logout button after login
- **Download Button**: Each document in search results has a download button

### Feature Flow
1. User first visit → Show login/register interface
2. Register/Login → Save token to localStorage
3. Access other features → Automatically add token to request headers
4. Logout → Clear token, return to login interface

## Deployment Notes

### Environment Variables
- `JWT_SECRET`: JWT signing secret (recommended to use AWS Secrets Manager)

### CDK Deployment
The following will be automatically created during deployment:
- UsersTable (DynamoDB)
- AuthFunction (Lambda)
- DownloadFunction (Lambda)
- Updated API Gateway routes

### Important Notes
1. Production should use stronger password hashing algorithm (e.g., bcrypt)
2. JWT secret should be managed using AWS Secrets Manager
3. Consider adding password strength validation
4. Consider adding email verification feature

## Security Features

1. **Password Hashing**: Uses SHA256 hashing (production should use bcrypt)
2. **JWT Signing**: Uses HMAC-SHA256 signing
3. **Token Expiration**: JWT tokens expire after 7 days
4. **Data Isolation**: Users can only access their own files
5. **Download Verification**: Verifies document ownership before download
