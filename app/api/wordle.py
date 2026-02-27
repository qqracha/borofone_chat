"""
Wordle API endpoints - Discord-like integration.

Endpoints:
- GET /wordle/game - Get current game state
- POST /wordle/guess - Make a guess
- GET /wordle/stats - Get player statistics
- POST /wordle/share - Generate shareable result
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback

from app.dependencies import get_current_user
from app.models import User
from app.services.wordle import (
    get_or_create_game,
    make_guess,
    get_stats,
    generate_share_text,
    is_valid_word,
)

router = APIRouter(prefix="/wordle", tags=["Wordle"])


class GuessRequest(BaseModel):
    guess: str
    language: Optional[str] = "ru"


class ShareRequest(BaseModel):
    language: Optional[str] = "ru"


@router.get("/game")
async def get_game(
    language: str = "ru",
    current_user: User = Depends(get_current_user),
):
    """Get current game state for today's Wordle."""
    try:
        game = await get_or_create_game(current_user.id, language)
        return {
            "success": True,
            "game": game.to_api_response(),
        }
    except Exception as e:
        print(f"❌ Wordle get_game error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get game: {str(e)}")


@router.post("/guess")
async def make_a_guess(
    request: GuessRequest,
    current_user: User = Depends(get_current_user),
):
    """Make a guess in today's Wordle game."""
    try:
        guess = request.guess.upper().strip()
        
        if len(guess) != 5:
            raise HTTPException(status_code=400, detail="Word must be 5 letters")
        
        # Validate word (allow any 5-letter word for flexibility)
        if not guess.isalpha():
            raise HTTPException(status_code=400, detail="Word must contain only letters")
        
        game, is_new = await make_guess(current_user.id, guess, request.language or "ru")
        
        return {
            "success": True,
            "game": game.to_api_response(),
            "is_new_guess": is_new,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Wordle make_guess error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to make guess: {str(e)}")


@router.get("/stats")
async def get_player_stats(
    language: str = "ru",
    current_user: User = Depends(get_current_user),
):
    """Get player statistics."""
    try:
        stats = await get_stats(current_user.id, language)
        return {
            "success": True,
            "stats": stats.to_dict(),
        }
    except Exception as e:
        print(f"❌ Wordle get_stats error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/share")
async def share_result(
    request: ShareRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate shareable result text."""
    try:
        game = await get_or_create_game(current_user.id, request.language or "ru")
        
        if not game.guesses:
            raise HTTPException(status_code=400, detail="No guesses made yet")
        
        share_text = generate_share_text(game, request.language or "ru")
        
        return {
            "success": True,
            "share_text": share_text,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Wordle share_result error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to share result: {str(e)}")
