# User Management Service

A comprehensive user management system with multi-tenant support, JWT authentication, and role-based access control for the LLM Multimodal Stack.

## 🚀 Features

### Core Functionality
- **User Management**: Create, read, update, delete users with full CRUD operations
- **Multi-tenant Support**: Isolated tenant environments with tenant-specific configurations
- **JWT Authentication**: Secure token-based authentication with access and refresh tokens
- **Role-based Access Control**: Admin, User, Guest, and Moderator roles with granular permissions
- **Session Management**: Redis-backed session storage with automatic cleanup
- **Password Security**: Bcrypt hashing with configurable complexity requirements

### Security Features
- **Rate Limiting**: Configurable rate limits for authentication endpoints
- **Account Lockout**: Automatic account lockout after failed login attempts
- **Audit Logging**: Comprehensive audit trail for all user actions
- **Password Policies**: Enforced password complexity and expiration
- **Session Security**: Secure session management with automatic expiration

### Advanced Features
- **Redis Caching**: High-performance caching for user data and sessions
- **Health Checks**: Comprehensive health monitoring for all dependencies
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Logging**: Structured logging with configurable levels

## 📋 Requirements

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker (optional)

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd services/user-management
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the service**
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build user-management
   ```

2. **Or build the image manually**
   ```bash
   docker build -t user-management .
   docker run -p 8006:8006 user-management
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name | `multimodal` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_DB` | Redis database number | `5` |
| `JWT_SECRET_KEY` | JWT signing key | `your-secret-key-change-in-production` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | `7` |
| `DEBUG` | Debug mode | `false` |

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "tenant_id": "optional-tenant-id"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "tenant_id": "optional-tenant-id",
  "remember_me": false
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <access-token>
```

### User Management Endpoints

#### Get Current User
```http
GET /api/v1/users/me
Authorization: Bearer <access-token>
```

#### Update Current User
```http
PUT /api/v1/users/me
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "first_name": "Updated Name",
  "preferences": {"theme": "dark"}
}
```

#### Change Password
```http
POST /api/v1/users/me/change-password
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "current_password": "OldPass123",
  "new_password": "NewPass123"
}
```

### Tenant Management Endpoints

#### Create Tenant (Admin)
```http
POST /api/v1/tenants
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "name": "Company Name",
  "description": "Company description",
  "domain": "company.com",
  "admin_email": "admin@company.com",
  "admin_username": "admin",
  "admin_password": "AdminPass123",
  "admin_first_name": "Admin",
  "admin_last_name": "User"
}
```

### Health Check

#### Service Health
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "user-management",
  "version": "2.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "dependencies": {
    "database": "connected",
    "cache": "connected"
  }
}
```

## 🔐 Authentication & Authorization

### JWT Tokens

The service uses JWT tokens for authentication:

- **Access Token**: Short-lived (30 minutes) for API access
- **Refresh Token**: Long-lived (7 days) for token renewal
- **Token Type**: Bearer token in Authorization header

### User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full system access, can manage all users and tenants |
| `moderator` | Can manage users within their tenant |
| `user` | Can manage their own profile |
| `guest` | Read-only access |

### Multi-tenant Isolation

- Users are isolated by tenant
- Cross-tenant access is restricted
- Admin users can access all tenants
- Tenant-specific configurations and settings

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## 🚀 Deployment

### Production Considerations

1. **Security**
   - Change default JWT secret key
   - Use HTTPS in production
   - Configure proper CORS origins
   - Enable rate limiting
   - Use strong database passwords

2. **Performance**
   - Configure Redis for optimal performance
   - Set up database connection pooling
   - Enable caching for frequently accessed data
   - Monitor memory usage

3. **Scalability**
   - Use load balancers for multiple instances
   - Configure Redis clustering for high availability
   - Set up database read replicas
   - Implement horizontal scaling

## 🔧 Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Maintain test coverage above 80%

### Code Quality Tools
```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection credentials
   - Ensure database exists

2. **Redis Connection Failed**
   - Check Redis is running
   - Verify Redis configuration
   - Check network connectivity

3. **JWT Token Invalid**
   - Verify JWT secret key
   - Check token expiration
   - Ensure proper token format

4. **Permission Denied**
   - Check user role and permissions
   - Verify tenant access rights
   - Ensure proper authentication

### Debug Mode
Enable debug mode for detailed logging:
```bash
export DEBUG=true
python main.py
```

## 📄 License

This project is part of the LLM Multimodal Stack and follows the same licensing terms.

---

**Version**: 2.0.0  
**Last Updated**: 2024-01-01  
**Maintainer**: LLM Multimodal Stack Team