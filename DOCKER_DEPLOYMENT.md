# Docker Deployment Guide

This guide covers deploying the Regulatory Intelligence Assistant using Docker.

## Overview

The application now supports both **development** and **production** Docker configurations:

- **Development**: Hot-reload enabled, debug mode, volume mounts for live code changes
- **Production**: Optimized builds, security hardening, production-ready nginx serving

## Quick Start

### Development Mode

```bash
# Start all services with hot reload
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

Frontend available at: http://localhost:5173  
Backend API available at: http://localhost:8000

### Production Mode

```bash
# Set up production environment
cp .env.production.example backend/.env.production
# Edit backend/.env.production with your secure values

# Build and start production services
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Stop services
docker compose -f docker-compose.prod.yml down
```

Frontend available at: http://localhost:80  
Backend API available at: http://localhost:8000

## Publishing to Docker Hub

### 1. Build Images

```bash
# Build frontend
docker build -t yourusername/regulatory-frontend:latest ./frontend

# Build backend
docker build -t yourusername/regulatory-backend:latest ./backend

# Build Neo4j with plugins
docker build -t yourusername/regulatory-neo4j:latest ./backend/neo4j
```

### 2. Tag with Version

```bash
# Tag with version number
docker tag yourusername/regulatory-frontend:latest yourusername/regulatory-frontend:1.0.0
docker tag yourusername/regulatory-backend:latest yourusername/regulatory-backend:1.0.0
docker tag yourusername/regulatory-neo4j:latest yourusername/regulatory-neo4j:1.0.0
```

### 3. Login to Docker Hub

```bash
docker login
```

### 4. Push Images

```bash
# Push frontend
docker push yourusername/regulatory-frontend:latest
docker push yourusername/regulatory-frontend:1.0.0

# Push backend
docker push yourusername/regulatory-backend:latest
docker push yourusername/regulatory-backend:1.0.0

# Push Neo4j
docker push yourusername/regulatory-neo4j:latest
docker push yourusername/regulatory-neo4j:1.0.0
```

## Production Deployment Checklist

- [ ] Update `backend/.env.production` with secure credentials
- [ ] Change default passwords for PostgreSQL, Neo4j, and any other services
- [ ] Update `CORS_ORIGINS` with your production domain(s)
- [ ] Set `VITE_API_URL` to your production backend URL
- [ ] Configure SSL/TLS certificates (use a reverse proxy like Traefik or nginx)
- [ ] Set up proper backup strategies for volumes
- [ ] Configure monitoring and logging solutions
- [ ] Review and adjust resource limits in docker-compose.prod.yml
- [ ] Enable firewall rules for production servers
- [ ] Set up CI/CD pipeline for automated builds

## Architecture

### Frontend (Production)
- **Base**: nginx:1.25-alpine
- **Build**: Multi-stage build with Node.js 20
- **Features**:
  - Production-optimized Vite build
  - Nginx serving static files
  - Gzip compression
  - Security headers
  - Health check endpoint
  - Non-root user for security

### Backend
- **Base**: python:3.11-slim
- **Features**:
  - FastAPI application
  - Database migrations
  - Service health checks
  - Automatic schema initialization

### Services
- **PostgreSQL**: Relational database for application data
- **Neo4j**: Graph database for regulatory relationships
- **Elasticsearch**: Full-text search engine
- **Redis**: Caching and session storage
- **Ollama**: Local LLM inference (optional in production)

## Environment Variables

### Frontend (Production Build)
- `VITE_API_URL`: Backend API URL (configured at build time)

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `NEO4J_URI`: Neo4j connection string
- `ELASTICSEARCH_URL`: Elasticsearch endpoint
- `REDIS_URL`: Redis connection string
- `CORS_ORIGINS`: Allowed CORS origins
- `APP_ENV`: Environment (development/production)
- `LOG_LEVEL`: Logging level

## Volume Management

### Persistent Data Volumes
- `postgres_data`: PostgreSQL database files
- `neo4j_data`: Neo4j graph database
- `elasticsearch_data`: Elasticsearch indices
- `redis_data`: Redis persistence
- `ollama_data`: Ollama models and cache

### Backup Volumes

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U postgres regulatory_db > backup.sql

# Backup Neo4j
docker compose exec neo4j neo4j-admin dump --database=neo4j --to=/data/neo4j-backup.dump

# Restore PostgreSQL
docker compose exec -T postgres psql -U postgres regulatory_db < backup.sql

# Restore Neo4j
docker compose exec neo4j neo4j-admin load --database=neo4j --from=/data/neo4j-backup.dump
```

## Troubleshooting

### Check Service Health

```bash
# Development
docker compose ps

# Production
docker compose -f docker-compose.prod.yml ps
```

### View Service Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f frontend
docker compose logs -f backend
```

### Restart Services

```bash
# Restart specific service
docker compose restart frontend

# Rebuild and restart
docker compose up -d --build frontend
```

### Common Issues

**Frontend can't reach backend:**
- Check CORS_ORIGINS includes frontend URL
- Verify backend health: `curl http://localhost:8000/health`
- Check network connectivity between containers

**Database connection errors:**
- Ensure services started in correct order (dependencies)
- Check health checks are passing
- Verify environment variables are set correctly

**Out of disk space:**
- Clean up unused images: `docker image prune -a`
- Clean up volumes: `docker volume prune`
- Check volume sizes: `docker system df`

## Security Best Practices

1. **Never use default passwords in production**
2. **Use secrets management** (Docker secrets, HashiCorp Vault, etc.)
3. **Run containers as non-root users** (already configured)
4. **Keep images updated** with security patches
5. **Use TLS/SSL** for all external connections
6. **Limit container resources** to prevent DoS
7. **Enable audit logging** for compliance
8. **Use private registries** for proprietary code
9. **Scan images for vulnerabilities** (use `docker scan`)
10. **Implement network segmentation** with Docker networks

## Monitoring

Consider integrating:
- **Prometheus + Grafana**: Metrics and dashboards
- **ELK Stack**: Centralized logging
- **Sentry**: Error tracking
- **Uptime monitoring**: Health check endpoints

## Next Steps

1. Set up CI/CD pipeline (GitHub Actions, GitLab CI, Jenkins)
2. Configure reverse proxy with SSL (Traefik, nginx, Caddy)
3. Implement blue-green or rolling deployments
4. Set up automated backups
5. Configure monitoring and alerting
6. Document runbooks for common operations
