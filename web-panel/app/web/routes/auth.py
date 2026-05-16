from fastapi import APIRouter, Request, Form, HTTPException, Depends, status, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from app.core.security import verify_admin_credentials, create_access_token
from app.api.schemas.auth import User
from app.api.deps import get_current_user
from app.config import get_settings
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="", tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page."""
    settings = get_settings()
    return templates.TemplateResponse("login.html", {
        "request": request,
        "app_name": settings.APP_NAME
    })


@router.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission."""
    if not verify_admin_credentials(username, password):
        return templates.TemplateResponse("login.html", {
            "request": None,
            "app_name": get_settings().APP_NAME,
            "error": "Usuário ou senha incorretos"
        }, status_code=401)
    
    access_token = create_access_token(data={"sub": username})
    
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600,
        samesite="lax"
    )
    return response


@router.get("/logout")
async def logout():
    """Handle logout."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response