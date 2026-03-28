import random
import copy
import math

COLORS = ['Red', 'Blue', 'Green', 'Yellow']
VALUES = [str(i) for i in range(10)] + ['Skip']

def evaluate(state, ai_player_index, strategy='baseline'):
    winner = state.get_winner()
    if winner == ai_player_index:
        return 1000
    elif winner != -1:
        return -1000 # Opponent won

    ai_hand = state.player_hands[ai_player_index]
    opp1_hand = state.player_hands[(ai_player_index + 1) % 3]
    opp2_hand = state.player_hands[(ai_player_index + 2) % 3]

    c_ai = len(ai_hand)
    c_opp = (len(opp1_hand) + len(opp2_hand)) / 2.0
    s_count = sum(1 for card in ai_hand if card.value == 'Skip')

    if strategy == 'defensive':
        return 50 - 3 * c_ai + 4 * c_opp + 5 * s_count
    elif strategy == 'offensive':
        return 50 - 8 * c_ai + 1 * c_opp + 1 * s_count
    else:
        return 50 - 5 * c_ai + 2 * c_opp + 3 * s_count

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def __repr__(self):
        return f"{self.color} {self.value}"

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.color == other.color and self.value == other.value
        return False

    def __hash__(self):
        return hash((self.color, self.value))
    
    def to_dict(self):
        return {"color": self.color, "value": self.value}

    @staticmethod
    def from_dict(d):
        return Card(d['color'], d['value'])

def generate_full_deck():
    deck = []
    for color in COLORS:
        for value in VALUES:
            deck.append(Card(color, value))
    return deck

class GameState:
    def __init__(self, player_hands, top_card, deck, current_turn=0):
        self.player_hands = player_hands 
        self.top_card = top_card
        self.deck = deck
        self.current_turn = current_turn

    def to_dict(self, ai_player_index=None):
        data = {
            "player_hands": [[c.to_dict() for c in hand] for hand in self.player_hands],
            "top_card": self.top_card.to_dict(),
            "deck_count": len(self.deck),
            "current_turn": self.current_turn,
            "is_terminal": self.is_terminal(),
            "winner": self.get_winner()
        }
        if ai_player_index is not None:
             opp1 = (ai_player_index + 1) % 3
             opp2 = (ai_player_index + 2) % 3
             data['ai_cards'] = [c.to_dict() for c in self.player_hands[ai_player_index]]
             data['opponent1_cards'] = len(self.player_hands[opp1])
             data['opponent2_cards'] = len(self.player_hands[opp2])
        return data

    def is_terminal(self):
        for hand in self.player_hands:
            if len(hand) == 0:
                return True
        return False

    def get_winner(self):
        for i, hand in enumerate(self.player_hands):
            if len(hand) == 0:
                return i
        return -1

    def clone(self):
        return GameState(
            [list(hand) for hand in self.player_hands],
            self.top_card,
            list(self.deck),
            self.current_turn
        )

def get_valid_moves(hand, top_card):
    valid_moves = []
    for card in hand:
        if card.color == top_card.color or card.value == top_card.value:
            valid_moves.append(card)
    return valid_moves

def apply_move(state: GameState, move):
    new_state = state.clone()
    p_idx = new_state.current_turn

    if move == 'Draw':
        if len(new_state.deck) > 0:
            drawn = new_state.deck.pop(0)
            new_state.player_hands[p_idx].append(drawn)
        new_state.current_turn = (new_state.current_turn + 1) % 3
    else:
        try:
            new_state.player_hands[p_idx].remove(move)
        except ValueError:
            pass 

        new_state.top_card = move

        if move.value == 'Skip':
            new_state.current_turn = (new_state.current_turn + 2) % 3
        else:
            new_state.current_turn = (new_state.current_turn + 1) % 3

    return new_state

def apply_chance_draw(state: GameState, drawn_card: Card):
    new_state = state.clone()
    p_idx = new_state.current_turn
    try:
        new_state.deck.remove(drawn_card)
    except ValueError:
        pass

    new_state.player_hands[p_idx].append(drawn_card)
    new_state.current_turn = (new_state.current_turn + 1) % 3
    return new_state

def setup_game():
    deck = generate_full_deck()
    random.shuffle(deck)

    player_hands = [[], [], []]
    for _ in range(5): 
        for i in range(3):
            player_hands[i].append(deck.pop(0))

    top_card = deck.pop(0)
    while top_card.value == 'Skip':
        deck.append(top_card)
        random.shuffle(deck)
        top_card = deck.pop(0)

    return GameState(player_hands, top_card, deck, current_turn=0)

def minimax(state: GameState, depth, ai_player_index):
    if state.is_terminal() or depth == 0:
        return evaluate(state, ai_player_index, 'defensive')

    is_maximizing = (state.current_turn == ai_player_index)
    valid_moves = get_valid_moves(state.player_hands[state.current_turn], state.top_card)

    if not valid_moves:
        child = apply_move(state, 'Draw')
        return minimax(child, depth - 1, ai_player_index)

    if is_maximizing:
        best_val = -math.inf
        for move in valid_moves:
            child = apply_move(state, move)
            val = minimax(child, depth - 1, ai_player_index)
            best_val = max(best_val, val)
        return best_val
    else:
        best_val = math.inf
        for move in valid_moves:
            child = apply_move(state, move)
            val = minimax(child, depth - 1, ai_player_index)
            best_val = min(best_val, val)
        return best_val

def get_best_move_minimax(state: GameState, depth, ai_player_index):
    valid_moves = get_valid_moves(state.player_hands[state.current_turn], state.top_card)
    if not valid_moves:
        return 'Draw', [{'action': 'Draw', 'score': 0}]

    best_val = -math.inf
    best_move = None
    scores = []

    for move in valid_moves:
        child = apply_move(state, move)
        val = minimax(child, depth - 1, ai_player_index)
        scores.append({'action': move.to_dict(), 'score': val})
        if val > best_val:
            best_val = val
            best_move = move

    if best_move is None:
        best_move = sorted(valid_moves, key=lambda x: str(x.value))[0]

    return best_move, scores

def expectimax(state: GameState, depth, ai_player_index):
    if state.is_terminal() or depth == 0:
        return evaluate(state, ai_player_index, 'offensive')

    is_maximizing = (state.current_turn == ai_player_index)
    valid_moves = get_valid_moves(state.player_hands[state.current_turn], state.top_card)

    if is_maximizing:
        if not valid_moves:
            return chance_node(state, depth, ai_player_index) 

        best_val = -math.inf
        for move in valid_moves:
            child = apply_move(state, move)
            val = expectimax(child, depth - 1, ai_player_index)
            best_val = max(best_val, val)
        return best_val
    else: 
        if not valid_moves:
            return chance_node(state, depth, ai_player_index)

        avg_val = 0
        for move in valid_moves:
            child = apply_move(state, move)
            avg_val += expectimax(child, depth - 1, ai_player_index)
        return avg_val / len(valid_moves)

def chance_node(state: GameState, depth, ai_player_index):
    if not state.deck:
        return evaluate(state, ai_player_index, 'offensive')

    expected_value = 0
    unique_cards = set(state.deck)
    for card in unique_cards:
        prob = state.deck.count(card) / len(state.deck)
        child = apply_chance_draw(state, card)
        expected_value += prob * expectimax(child, depth - 1, ai_player_index)

    return expected_value

def get_best_move_expectimax(state: GameState, depth, ai_player_index):
    valid_moves = get_valid_moves(state.player_hands[state.current_turn], state.top_card)
    if not valid_moves:
        return 'Draw', [{'action': 'Draw', 'score': 0}]

    best_val = -math.inf
    best_move = None
    scores = []

    for move in valid_moves:
        child = apply_move(state, move)
        val = expectimax(child, depth - 1, ai_player_index)
        scores.append({'action': move.to_dict(), 'score': val})
        if val > best_val:
            best_val = val
            best_move = move

    if best_move is None:
        best_move = valid_moves[0]

    return best_move, scores
