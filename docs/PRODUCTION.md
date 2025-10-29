# Production MCP Deployment Guide

This guide covers deploying MCP applications to production with best practices, monitoring, and scalability.

## 🏭 Production Features

The MCP Sandbox includes production-ready features:

### ✅ Core Production Features
- **Error Handling**: Comprehensive exception handling with retry logic
- **Request Metrics**: Track success rates, latency, and errors
- **Configuration Management**: JSON-based server configuration  
- **Health Monitoring**: Server health checks and automatic recovery
- **Structured Logging**: File-based logging with request correlation
- **Graceful Degradation**: Continues operating when servers fail

### ✅ Reliability Features
- **Retry Logic**: Exponential backoff for API failures
- **Timeout Handling**: Request and connection timeouts
- **Circuit Breakers**: Disable unhealthy servers automatically
- **Connection Pooling**: Reuse MCP server connections

## 🚀 Quick Start

### 1. Run the Application

```bash
# Install dependencies (if not already done)
poetry install

# Run demo
make demo
# OR: poetry run demo

# Run interactive chat
make chat
# OR: poetry run chat
```

### 2. Configuration

The configuration file `config/mcp.json`:

```json
{
  "servers": [
    {
      "name": "sqlite-database",
      "script_path": "mcp_sandbox.server",
      "enabled": true,
      "timeout": 30,
      "max_retries": 3,
      "health_check_interval": 60,
      "metadata": {
        "description": "SQLite database MCP server",
        "version": "1.0.0"
      }
    }
  ],
  "log_level": "INFO"
}
```

### 3. Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="your-key-here"

# Optional  
export MCP_CONFIG_PATH="config/mcp.json"
export LOG_LEVEL="INFO"
```

## 📊 Production Deployment Patterns

### 1. Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app \
    && mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app/logs /app/data

USER appuser

# Run application
CMD ["poetry", "run", "demo"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  mcp-app:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config:ro
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

**Build and run:**
```bash
# Build image
docker-compose build

# Run service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### 2. Kubernetes Deployment

**k8s/deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-app
  labels:
    app: mcp-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-app
  template:
    metadata:
      labels:
        app: mcp-app
    spec:
      containers:
      - name: mcp-app
        image: your-registry/mcp-app:latest
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: anthropic-secret
              key: api-key
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: mcp-config
      - name: data
        persistentVolumeClaim:
          claimName: mcp-data-pvc
```

**k8s/secret.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: anthropic-secret
type: Opaque
data:
  # Base64 encoded API key
  api-key: <base64-encoded-key>
```

**k8s/configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-config
data:
  mcp.json: |
    {
      "servers": [
        {
          "name": "sqlite-database",
          "script_path": "mcp_sandbox.server",
          "enabled": true,
          "timeout": 30,
          "max_retries": 3,
          "health_check_interval": 60,
          "metadata": {
            "description": "SQLite database MCP server",
            "version": "1.0.0"
          }
        }
      ],
      "log_level": "INFO"
    }
```

**Deploy:**
```bash
# Create secret (encode your API key first)
echo -n 'your-api-key' | base64
kubectl apply -f k8s/secret.yaml

# Apply configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=mcp-app
kubectl logs -f deployment/mcp-app
```

### 3. AWS ECS Deployment

**task-definition.json:**
```json
{
  "family": "mcp-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "mcp-app",
      "image": "your-registry/mcp-app:latest",
      "essential": true,
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:anthropic-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mcp-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## 📊 Monitoring and Observability

### 1. Metrics Collection

The `MCPClient` tracks:
- Request count and success rate
- Average response latency
- Error rates by type
- Server health status
- Tool usage patterns

Access metrics via:
```python
# In chat, use /metrics command
# OR programmatically:
from mcp_sandbox import MCPClient

client = MCPClient()
await client.initialize()
metrics = client.get_metrics_summary()
print(metrics)
```

### 2. Logging

Logs are written to `logs/mcp.log`:

```json
{
  "timestamp": "2025-10-29T10:30:45.123Z",
  "level": "INFO",
  "component": "MCPClient",
  "request_id": "req_1698576645123",
  "message": "Request completed",
  "duration_seconds": 1.23,
  "tools_used": ["execute_sql_query"]
}
```

### 3. Health Checks

Implement health check endpoint:

```python
from mcp_sandbox import MCPClient

async def health_check():
    client = MCPClient()
    await client.initialize()
    
    metrics = client.get_metrics_summary()
    is_healthy = metrics.get("successful", 0) > 0
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "metrics": metrics
    }
```

## 🔒 Security Best Practices

### 1. API Key Management

**DO:**
- ✅ Use environment variables or secrets management
- ✅ Rotate keys regularly
- ✅ Use separate keys for dev/staging/prod
- ✅ Monitor API usage and set alerts

**DON'T:**
- ❌ Hardcode keys in code
- ❌ Commit keys to git
- ❌ Share keys across environments
- ❌ Use keys without monitoring

### 2. Input Validation

```python
# Sanitize user inputs
def sanitize_input(user_input: str) -> str:
    # Remove potentially harmful content
    # Implement max length checks
    # Validate against allowed patterns
    return sanitized_input
```

### 3. Rate Limiting

```python
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = []
    
    def is_allowed(self) -> bool:
        now = datetime.now()
        cutoff = now - self.window
        
        # Remove old requests
        self.requests = [r for r in self.requests if r > cutoff]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

## 🚀 Scaling Strategies

### 1. Horizontal Scaling

- Deploy multiple instances behind load balancer
- Use stateless design
- Implement session affinity if needed
- Cache frequently accessed data

### 2. Performance Optimization

```python
# Connection pooling
# Async/await for concurrent requests
# Cache MCP tool definitions
# Batch similar requests
```

### 3. Cost Optimization

- Monitor token usage
- Implement request caching
- Use appropriate model sizes
- Set up usage alerts

## 🐛 Troubleshooting

### Common Issues

1. **MCP Server Connection Failures**
   ```bash
   # Check server is accessible
   python -m mcp_sandbox.server
   
   # Verify configuration
   cat config/mcp.json | jq
   
   # Check logs
   tail -f logs/mcp.log
   ```

2. **API Rate Limits**
   ```python
   # Check metrics for rate limit errors
   # Implement exponential backoff (already included)
   # Consider request queuing
   ```

3. **High Latency**
   ```python
   # Review metrics for slow requests
   # Optimize database queries
   # Enable caching
   # Scale horizontally
   ```

## 📈 Production Checklist

### Pre-Deployment
- [ ] API keys configured securely
- [ ] Configuration validated
- [ ] Logging configured
- [ ] Error handling tested
- [ ] Performance benchmarked
- [ ] Security review completed

### Deployment
- [ ] Health checks passing
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Backup strategy in place
- [ ] Rollback plan ready

### Post-Deployment
- [ ] Monitor error rates
- [ ] Track performance metrics
- [ ] Review logs regularly
- [ ] Optimize based on usage
- [ ] Plan capacity scaling

## 📚 Additional Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [12 Factor App Methodology](https://12factor.net/)
- [Production Best Practices](https://docs.python.org/3/library/logging.html)

---

**Ready for Production!** 🎉

This setup provides enterprise-grade MCP deployment with proper error handling, monitoring, and scalability.