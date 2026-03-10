import json
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import attachments, rooms, voice_rooms, wordle
from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.http import router as http_router
from app.api.ws import router as ws_router
from app.infra.db import engine
from app.settings import settings


def _list_media_files(directory, suffixes: tuple[str, ...], *, exclude_readme: bool = False) -> list[str]:
    if not directory.is_dir():
        return []

    items = []
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        if not entry.name.lower().endswith(suffixes):
            continue
        if exclude_readme and entry.name.lower().startswith('readme'):
            continue
        items.append(entry.name)
    return items


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    from app.infra.redis import close_redis

    await close_redis()
    await engine.dispose()


app = FastAPI(
    title='Borofone Chat API',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['Set-Cookie'],
)


@app.middleware('http')
async def add_cross_origin_headers(request: Request, call_next: Callable):
    response: Response = await call_next(request)
    if request.url.path.startswith('/games/'):
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    return response


@app.get('/app-config.js', include_in_schema=False)
async def app_config_js() -> Response:
    payload = {
        'apiUrl': settings.resolved_public_api_base_url,
        'wsUrl': settings.resolved_public_ws_base_url,
        'routes': {
            'main': settings.main_page_route,
            'login': settings.login_page_route,
            'register': settings.register_page_route,
        },
        'uploads': {
            'avatarsBasePath': settings.avatar_public_path,
            'attachmentsBasePath': settings.attachments_public_path,
        },
    }
    return Response(
        content=f'window.__BOROFONE_RUNTIME_CONFIG__ = {json.dumps(payload, ensure_ascii=False)};\n',
        media_type='application/javascript',
    )


@app.get('/')
async def root():
    return RedirectResponse(url=settings.main_page_path.lstrip('/'))


@app.get('/favicon.ico')
async def favicon():
    return FileResponse(settings.favicon_file)


@app.get('/api/emoji')
async def list_custom_emojis():
    return {'emojis': _list_media_files(settings.emoji_path, ('.gif', '.png', '.jpg', '.jpeg', '.webp'))}


@app.get('/api/stickers')
async def list_stickers():
    return {
        'stickers': _list_media_files(
            settings.stickers_path,
            ('.png', '.jpg', '.jpeg', '.gif', '.webp'),
            exclude_readme=True,
        )
    }


@app.get('/api/gifs')
async def list_gifs():
    return {
        'gifs': _list_media_files(
            settings.gifs_path,
            ('.gif', '.webp'),
            exclude_readme=True,
        )
    }


@app.get('/api/media')
async def list_all_media():
    return {
        'emojis': _list_media_files(settings.emoji_path, ('.gif', '.png', '.jpg', '.jpeg', '.webp')),
        'stickers': _list_media_files(
            settings.stickers_path,
            ('.png', '.jpg', '.jpeg', '.gif', '.webp'),
            exclude_readme=True,
        ),
        'gifs': _list_media_files(
            settings.gifs_path,
            ('.gif', '.webp'),
            exclude_readme=True,
        ),
    }


app.include_router(http_router, tags=['HTTP'])
app.include_router(ws_router, tags=['Websocket'])
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(rooms.router)
app.include_router(attachments.router)
app.include_router(voice_rooms.router)
app.include_router(wordle.router)

settings.uploads_path.mkdir(parents=True, exist_ok=True)

app.mount('/uploads', StaticFiles(directory=settings.uploads_path), name='uploads')
app.mount('/', StaticFiles(directory=settings.pages_path, html=True), name='pages')
