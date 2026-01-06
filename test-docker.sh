#!/bin/bash
# Docker test script for Math24 application

set -e

echo "🐳 Math24 Docker Test Suite"
echo "============================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check Docker is running
echo "📦 Test 1: Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is not running"
    exit 1
fi

# Test 2: Validate docker-compose.yml
echo ""
echo "📝 Test 2: Validating docker-compose.yml..."
if docker compose config --quiet 2>&1 | grep -q "WARN"; then
    echo -e "${YELLOW}⚠${NC} docker-compose.yml has warnings (non-critical)"
else
    echo -e "${GREEN}✓${NC} docker-compose.yml is valid"
fi

# Test 3: Check .env file
echo ""
echo "🔑 Test 3: Checking environment variables..."
if [ -f backend/.env ]; then
    if grep -q "GEMINI_API_KEY" backend/.env; then
        echo -e "${GREEN}✓${NC} .env file exists with GEMINI_API_KEY"
    else
        echo -e "${RED}✗${NC} GEMINI_API_KEY not found in .env"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} backend/.env file not found"
    exit 1
fi

# Test 4: Build images
echo ""
echo "🏗️  Test 4: Building Docker images..."
if docker compose build --quiet; then
    echo -e "${GREEN}✓${NC} Images built successfully"
else
    echo -e "${RED}✗${NC} Image build failed"
    exit 1
fi

# Test 5: Start containers
echo ""
echo "🚀 Test 5: Starting containers..."
docker compose up -d
sleep 5

# Test 6: Check container status
echo ""
echo "📊 Test 6: Checking container status..."
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓${NC} Containers are running"
else
    echo -e "${RED}✗${NC} Containers failed to start"
    docker compose logs
    exit 1
fi

# Test 7: Backend health check
echo ""
echo "🏥 Test 7: Testing backend health..."
if curl -sf http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Backend is healthy"
else
    echo -e "${RED}✗${NC} Backend health check failed"
    docker compose logs backend
    exit 1
fi

# Test 8: Frontend health check
echo ""
echo "🏥 Test 8: Testing frontend health..."
if curl -sf http://localhost/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Frontend is healthy"
else
    echo -e "${RED}✗${NC} Frontend health check failed"
    docker compose logs frontend
    exit 1
fi

# Test 9: Backend API functionality
echo ""
echo "🧪 Test 9: Testing backend API..."
response=$(curl -sf -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"numbers":[3,8,3,8],"expression":"8/(3-8/3)","target":24}')

if echo "$response" | grep -q '"valid":true'; then
    echo -e "${GREEN}✓${NC} Backend API working correctly"
else
    echo -e "${RED}✗${NC} Backend API test failed"
    echo "Response: $response"
    exit 1
fi

# Test 10: Frontend serving
echo ""
echo "🌐 Test 10: Testing frontend..."
if curl -sf http://localhost/ | grep -q "<title>"; then
    echo -e "${GREEN}✓${NC} Frontend serving HTML correctly"
else
    echo -e "${RED}✗${NC} Frontend test failed"
    exit 1
fi

# Summary
echo ""
echo "============================"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "📍 Access your application:"
echo "   Frontend: http://localhost"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🛠️  Useful commands:"
echo "   View logs:    docker compose logs -f"
echo "   Stop:         docker compose down"
echo "   Restart:      docker compose restart"
echo "   Rebuild:      docker compose up -d --build"
echo ""
