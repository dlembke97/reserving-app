from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import reserving

app = FastAPI(
    title="Reserving App API",
    description="API for reserving analytics using chainladder",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reserving.router, prefix="/reserving", tags=["reserving"])


@app.get("/")
async def root():
    return {"message": "Reserving App API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
