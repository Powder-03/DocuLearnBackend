# Quick Start Guide

## Prerequisites

1. Docker and Docker Compose installed
2. AWS Cognito User Pool configured
3. Your AI microservices (generation_service and rag_service) ready

## Step 1: Configure Cognito

1. Go to AWS Cognito Console
2. Create/select your User Pool
3. Note down:
   - User Pool ID
   - Region
   - Client ID
   - Client Secret
   - Domain prefix

4. Configure App Client:
   - Add callback URL: `http://localhost:8000/api/v1/auth/callback`
   - Add sign-out URL: `http://localhost:3000`
   - Enable OAuth 2.0 grants: Authorization code grant
   - Enable OAuth scopes: email, openid, profile

## Step 2: Setup Environment

1. Copy the `.env` file and fill in your Cognito details:

```bash
# Database
DATABASE_URL=postgresql+psycopg://admin:supersecret@db:5432/learning_saas_db

# Cognito (REPLACE THESE)
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=your_client_id_here
COGNITO_CLIENT_SECRET=your_client_secret_here
COGNITO_DOMAIN=your-domain-prefix.auth.us-east-1.amazoncognito.com
REDIRECT_URI=http://localhost:8000/api/v1/auth/callback

# Internal Services (adjust if needed)
GENERATION_SERVICE_URL=http://generation_service:8001
RAG_SERVICE_URL=http://rag_service:8002
```

## Step 3: Update Docker Compose

If you have your own docker-compose.yml, add the backend service:

```yaml
services:
  backend:
    build: ./backend  # or ./DocuLearn_Backend
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    depends_on:
      - db
    networks:
      - app-network

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: supersecret
      POSTGRES_DB: learning_saas_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  # Add your existing services here...
```

## Step 4: Build and Run

```bash
# Build the service
docker-compose build backend

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Verify database migration ran
docker-compose exec backend alembic current
```

## Step 5: Test Authentication

1. Open browser to: `http://localhost:8000/api/v1/auth/login`
2. You should be redirected to Cognito Hosted UI
3. Sign up or log in
4. After successful login, you'll be redirected to frontend
5. Check cookie was set (in browser DevTools → Application → Cookies)

## Step 6: Test API Endpoints

```bash
# Check health
curl http://localhost:8000/health

# Check auth status (should show authenticated: false without cookie)
curl http://localhost:8000/api/v1/auth/status

# After logging in via browser, test protected endpoint
curl http://localhost:8000/api/v1/users/me \
  -H "Cookie: access_token=YOUR_TOKEN_FROM_BROWSER"
```

## Step 7: Update Frontend

Update your frontend to use these endpoints:

```javascript
// Login
window.location.href = 'http://localhost:8000/api/v1/auth/login';

// Logout
await fetch('http://localhost:8000/api/v1/auth/logout', {
  method: 'POST',
  credentials: 'include'  // Important for cookies!
});

// Call protected endpoints
const response = await fetch('http://localhost:8000/api/v1/users/me', {
  credentials: 'include'  // Sends cookies
});
```

## Troubleshooting

### Database connection error
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart db

# Run migrations manually
docker-compose exec backend alembic upgrade head
```

### Cognito redirect not working
- Verify callback URL matches exactly in Cognito console
- Check COGNITO_DOMAIN doesn't have `https://` prefix
- Ensure OAuth scopes are enabled

### CORS errors
- Verify FRONTEND_URL in .env matches your actual frontend URL
- Check browser console for specific CORS error details

### Token verification fails
- Confirm COGNITO_USER_POOL_ID and COGNITO_REGION are correct
- Check JWKS endpoint is accessible: `https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}/.well-known/jwks.json`

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Production Deployment

Before deploying to production:

1. ✅ Set `COOKIE_SECURE=True` in .env
2. ✅ Update `REDIRECT_URI` to production URL
3. ✅ Add production callback URL to Cognito
4. ✅ Use environment-specific secrets (AWS Secrets Manager)
5. ✅ Enable HTTPS on your load balancer
6. ✅ Configure proper CORS origins
7. ✅ Add rate limiting
8. ✅ Set up monitoring and alerts

## Next Steps

1. Integrate with your existing AI services
2. Add more proxy endpoints as needed
3. Implement refresh token rotation
4. Add user profile management endpoints
5. Set up CI/CD pipeline
