# Reserving App

A monorepo application for reserving analytics using chainladder methods, built with Remix (TypeScript) + Ant Design frontend and FastAPI (Python) backend.

## 🏗️ Architecture

- **Frontend**: Remix (TypeScript) with Ant Design components
- **Backend**: FastAPI (Python 3.12) with chainladder analytics
- **Package Managers**: npm (frontend), pipenv (backend)
- **Development**: Docker Compose or direct local development

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- pipenv
- Docker & Docker Compose (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Start both services
docker-compose up --build

# Frontend will be available at: http://localhost:3000
# Backend API will be available at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup

```bash
cd api

# Install pipenv if you don't have it
pip install --user pipenv

# Install dependencies and create virtual environment
pipenv install

# Activate virtual environment and start the development server
pipenv run uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
repo-root/
├── frontend/                 # Remix frontend application
│   ├── app/
│   │   ├── routes/          # File-based routing
│   │   ├── components/      # React components
│   │   └── utils/           # Utility functions
│   ├── package.json
│   └── remix.config.ts
├── api/                      # FastAPI backend
│   ├── app/
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   └── main.py          # Application entry point
│   ├── tests/               # Test files
│   ├── Pipfile              # pipenv dependencies
│   └── Dockerfile
├── infra/                    # Infrastructure files
│   └── docker-compose.yml
└── .github/workflows/        # CI/CD pipelines
```

## 🔧 Development

### Backend Development

The backend provides a REST API with the following endpoints:

- `POST /reserving/analyze` - Analyze loss triangle data
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

#### API Usage

```bash
# Test the API with a sample CSV (PowerShell)
# Option 1: Install curl for Windows (easiest)
# Download curl from: https://curl.se/windows/ or use winget: winget install cURL.cURL

# Option 2: Use Python to test the API
python -c "
import requests
files = {'csv': open('api/sample_triangle.csv', 'rb')}
data = {'origin_col': 'origin', 'dev_col': 'dev', 'value_col': 'value', 'cumulative': 'true'}
response = requests.post('http://localhost:8000/reserving/analyze', files=files, data=data)
print(response.json())
"

# Option 3: Use curl if you have it installed
# curl -X POST "http://localhost:8000/reserving/analyze" -F "csv=@api/sample_triangle.csv" -F "origin_col=origin" -F "dev_col=dev" -F "value_col=value" -F "cumulative=true"
```

#### Running Tests

```bash
cd api
pipenv install --dev
pipenv run pytest tests/ -v
```

### Frontend Development

The frontend is built with Remix and provides:

- Dashboard with overview statistics
- Triangle upload form with CSV processing
- Results display with Ant Design components

#### Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run typecheck # TypeScript type checking
```

## 📊 Data Format

The application expects CSV files with the following structure:

```csv
origin,dev,value
2020,1,1000
2020,2,1500
2020,3,1800
2021,1,1200
2021,2,1600
2022,1,1100
```

- `origin`: Origin period (e.g., accident year)
- `dev`: Development period (e.g., months, quarters)
- `value`: Loss amounts (cumulative or incremental)

## 🧪 Testing

### Backend Tests

```bash
cd api
pipenv run pytest tests/ -v --tb=short
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 🚢 Deployment

### Backend Deployment

```bash
cd api
pipenv install --deploy
pipenv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Deployment

```bash
cd frontend
npm run build
npm run start
```

## 🔄 CI/CD

GitHub Actions automatically:

- Lints and builds the frontend
- Runs backend tests
- Validates TypeScript types
- Ensures code quality on every PR

## 📝 Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# API Configuration
API_BASE_URL=http://localhost:8000

# Frontend Configuration
NODE_ENV=development

# Backend Configuration
PYTHONPATH=./api
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📋 Roadmap

- [ ] Generate OpenAPI types and typed API client
- [ ] Add Playwright E2E tests
- [ ] Extend backend with tail factor and BF/ELR prior support
- [ ] Add more reserving methods
- [ ] Implement user authentication
- [ ] Add data persistence layer

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.