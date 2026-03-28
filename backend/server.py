from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import game_logic
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

origins = os.getenv("FRONTEND_URL", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_game = None

@app.post("/api/start")
def start_game():
    global current_game
    current_game = game_logic.setup_game()
    return current_game.to_dict()

@app.get("/api/state")
def get_state():
    if current_game is None:
        return {"started": False}
    return current_game.to_dict()

class PlayCardRequest(BaseModel):
    card_index: int

@app.post("/api/play")
def play_move(req: PlayCardRequest = None, draw: bool = False):
    global current_game
    if current_game is None:
        raise HTTPException(status_code=400, detail="Game not started")

    p_idx = current_game.current_turn
    hand = current_game.player_hands[p_idx]
    
    if draw:
        current_game = game_logic.apply_move(current_game, 'Draw')
        return {"state": current_game.to_dict()}

    if req is None or req.card_index < 0 or req.card_index >= len(hand):
        raise HTTPException(status_code=400, detail="Invalid card index")

    card = hand[req.card_index]
    valid_moves = game_logic.get_valid_moves(hand, current_game.top_card)
    
    if card not in valid_moves:
        raise HTTPException(status_code=400, detail="Card is not valid to play")
    
    current_game = game_logic.apply_move(current_game, card)
    return {"state": current_game.to_dict()}

@app.post("/api/ai_turn")
def ai_turn(simulate_mode: bool = False):
    global current_game
    if current_game is None or current_game.is_terminal():
        return {"state": current_game.to_dict() if current_game else None}
    
    p_idx = current_game.current_turn
    depth_limit = 3
    scores = []
    move = 'Draw'
    
    if p_idx == 0:
        move, scores = game_logic.get_best_move_minimax(current_game, depth_limit, p_idx)
    elif p_idx == 1:
        move, scores = game_logic.get_best_move_expectimax(current_game, depth_limit, p_idx)
    elif p_idx == 2 and simulate_mode:
        move, scores = game_logic.get_best_move_minimax(current_game, depth_limit, p_idx)
    elif p_idx == 2 and not simulate_mode:
        raise HTTPException(status_code=400, detail="Not AI turn")

    current_game = game_logic.apply_move(current_game, move)
    return {
        "state": current_game.to_dict(),
        "action_taken": move.to_dict() if move != 'Draw' else 'Draw',
        "scores": scores
    }
