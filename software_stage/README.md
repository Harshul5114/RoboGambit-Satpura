This README provides a comprehensive overview of the **RoboGambit Autonomous Game Engine**, explaining the underlying logic, data structures, and optimizations used for the 6x6 chess variant.

---

# RoboGambit Engine: 6x6 Autonomous Chess

This engine is designed for a custom 6x6 chess variant. It utilizes a high-performance **Bitboard** representation, an **Alpha-Beta Pruning** search algorithm, and advanced speed optimizations like **Zobrist Hashing**.

## 1. Core Architecture

The engine is modularized into several key components:

* **`bitboard.py`**: The "brain" of the board representation. It stores piece positions as 64-bit integers (of which only 36 bits are used).
* **`moves.py`**: The move generator. It calculates legal moves for every piece type while ensuring the King is not left in check.
* **`game.py`**: The decision-making hub. It contains the search algorithm (`minimax`) and the board evaluation logic.
* **`constants.py`**: Stores piece values and Piece-Square Tables (PST).

---

## 2. Board Representation: Bitboards

Instead of using a standard 2D array for calculations, the engine uses **Bitboards**. Each piece type for each color has its own 64-bit integer.

* **Efficiency**: Operations like finding all pieces or checking occupancy are done using bitwise AND/OR/XOR, which are significantly faster than looping over an array.
* **LSB Extraction**: The engine uses Least Significant Bit (LSB) operations to quickly locate pieces on the board.

---

## 3. The Search Logic: Alpha-Beta Minimax

The engine looks ahead into the future to find the best move using the **Minimax algorithm with Alpha-Beta Pruning**.

1. **Minimax**: The engine assumes both players play optimally. It tries to maximize the score for White and minimize it for Black.
2. **Alpha-Beta Pruning**: This optimization allows the engine to "prune" (skip) branches of the search tree that it knows cannot possibly be better than a branch it has already evaluated.
3. **Move Ordering**: To make Pruning more effective, the engine sorts moves using a heuristic (captures first, then high-value pieces moving to good squares). This ensures the best moves are searched earlier, leading to more cutoffs.

---

## 4. Speed Optimization: Zobrist Hashing

To handle the complexity of deep searches, the engine implements **Incremental Zobrist Hashing** and a **Transposition Table (TT)**.

* **Transposition Table**: A global cache that remembers board positions the engine has already searched. If the engine reaches the same position via a different move order (a "transposition"), it looks up the result instantly instead of recalculating.
* **Incremental Updates**: Instead of hashing the whole board every time, the engine uses XOR operations to "toggle" pieces on and off a 64-bit hash key as they move. This makes the hashing process virtually instantaneous.

---

## 5. Evaluation Logic

The `evaluate` function determines how "good" a position is. It is not just about material; it uses a multi-factor approach:

1. **Material Weight**: Standard values (Pawn=100, Knight=300, etc.).
2. **Piece-Square Tables (PST)**: The engine rewards pieces for being in certain positions. For example, Knights are rewarded for being in the center, and Pawns are rewarded for advancing toward promotion.
3. **Terminal States**:
* **Checkmate**: Assigned a value of $\pm 100,000$ (adjusted by depth to find the quickest mate).
* **Stalemate**: Assigned a value of $0$ to ensure a winning engine doesn't accidentally draw.



---

## 6. Project Structure

| File | Description |
| --- | --- |
| `main.py` | Entry point for the application. |
| `ui.py` | Pygame-based interface for visualizing the game and playing against the bot. |
| `utils.py` | Helper functions for board notation (A1, B2) and `in_check` detection. |
| `bitboard.py` | Bitboard class and low-level bit manipulation. |
| `game.py` | Search algorithms and Transposition Table management. |
| `moves.py` | Legal move generation for all 10 piece types. |

---

## 7. How to Run

To play against the engine or watch it play against itself:

1. Ensure you have `pygame` and `numpy` installed:
```bash
pip install pygame numpy

```


2. Run the main file:
```bash
python main.py

```