from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes.auth import router as api_auth_router
from app.web.routes.auth import router as web_auth_router
from app.api.deps import get_current_user
from app.api.schemas.auth import User
from app.core.security import decode_access_token

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="app/web/templates")

# Include routers
app.include_router(api_auth_router)
app.include_router(web_auth_router)


@app.get("/", include_in_schema=False)
async def root():
    """Root redirect to dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    """Dashboard page (protected)."""
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    payload = decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=302)
    
    username = payload.get("sub")
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": {"username": username}
    })


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    if exc.status_code == 401:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": exc.detail
    }, status_code=exc.status_code)