


from typing import Tuple


def cell_to_coords(cell: str) -> Tuple[int, int]:
    """Convert a cell like 'A1' to (row, col) coordinates."""
    col = ord(cell[0].upper()) - ord('A')
    row = int(cell[1]) - 1
    return row, col

def parse_move(move: str) -> Tuple[int, int, int, int, int, int]:
    """Parse the move string into source and destination coordinates."""
    # format: "<piece_id>:<source_cell>-><destination_cell>=<promote_piece_id>"

    left, right = move.split("->")
    piece_id, source_cell = left.split(":")
    if "=" in right:
        destination_cell, promote_piece_id = right.split("=")
    else:
        destination_cell = right
        promote_piece_id = piece_id

    sr, sc = cell_to_coords(source_cell)
    dr, dc = cell_to_coords(destination_cell)

    return int(piece_id), sr, sc, dr, dc, int(promote_piece_id)

print(parse_move("3:C2->D4=5"))

