# chunk is a 2D array of 1 x chunk_width units
# so mm_block_unit_ht by chunk_width * mm_block_unit_wt tiles

def read_next_tile(
    row_in_mm_M_block_idx: int,
    chunk_col_in_tiles: int,
    mm_M_block_idx: int,
    advance_by_tiles: int,
    chunk_piece_size: int,
    chunk_width_in_tiles: int,
    mm_block_unit_ht: int
) -> tuple[int, int, int]:
    """
    Read the next tile from the chunk.
    """
    if advance_by_tiles < 0:
        raise ValueError("advance_by_tiles must be greater than 0")
    if advance_by_tiles == 0:
        return row_in_mm_M_block_idx, chunk_col_in_tiles, mm_M_block_idx

    # TODO: this can be simplified by using the modulo operator
    if advance_by_tiles >= chunk_piece_size:
        move_by_pieces = advance_by_tiles // chunk_piece_size
        advance_by_tiles -= move_by_pieces * chunk_piece_size
        mm_M_block_idx += move_by_pieces

    # TODO: this can be simplified by using the modulo operator
    if advance_by_tiles >= chunk_width_in_tiles:
        move_by_rows = advance_by_tiles // chunk_width_in_tiles
        new_row = row_in_mm_M_block_idx + move_by_rows
        advance_by_tiles -= move_by_rows * chunk_width_in_tiles
        if new_row >= mm_block_unit_ht:
            mm_M_block_idx += 1
            row_in_mm_M_block_idx = new_row % mm_block_unit_ht
        else:
            row_in_mm_M_block_idx = new_row

    new_col = chunk_col_in_tiles + advance_by_tiles
    if new_col >= chunk_width_in_tiles:
        row_in_mm_M_block_idx += 1
        if row_in_mm_M_block_idx >= mm_block_unit_ht:
            mm_M_block_idx += 1
            row_in_mm_M_block_idx = 0
        new_col = new_col % chunk_width_in_tiles

    return row_in_mm_M_block_idx, new_col, mm_M_block_idx

def how_many_tiles_to_read_formula(
    row_in_mm_M_block_idx: int,
    chunk_col_in_tiles: int,
    mm_M_block_idx: int,
    advance_by_tiles: int,
    last_mm_M_block_idx: int,
    chunk_piece_size: int,
    chunk_width_in_tiles: int
):
    current_tile_offset = (
        row_in_mm_M_block_idx * chunk_width_in_tiles + chunk_col_in_tiles
    )
    current_block_tiles_remaining = chunk_piece_size - current_tile_offset - 1
    future_blocks_tiles = (
        (last_mm_M_block_idx - mm_M_block_idx) * chunk_piece_size
    )
    all_tiles = current_block_tiles_remaining + future_blocks_tiles
    return 1 + all_tiles // advance_by_tiles

def read_tiles_granular(
    worker_id: int,
    start_row_in_mm_M_block_idx: int,
    start_chunk_col_in_tiles: int,
    start_mm_M_block_idx: int,
    advance_by_tiles: int,
    last_mm_M_block_idx: int,
    tile_granularity: int,
    chunk_piece_size: int,
    chunk_width_in_tiles: int,
    mm_block_unit_ht: int
):
    """
    Read the tiles granularly.
    """
    if tile_granularity <= 0:
        raise ValueError("tile_granularity must be greater than 0")
    if advance_by_tiles <= 0:
        raise ValueError("advance_by_tiles must be greater than 0")
    if last_mm_M_block_idx < start_mm_M_block_idx:
        raise ValueError(
            "last_mm_M_block_idx must be >= start_mm_M_block_idx"
        )

    (
        first_row_in_mm_M_block_idx,
        first_chunk_col_in_tiles,
        first_mm_M_block_idx
    ) = read_next_tile(
        start_row_in_mm_M_block_idx,
        start_chunk_col_in_tiles,
        start_mm_M_block_idx,
        worker_id,
        chunk_piece_size,
        chunk_width_in_tiles,
        mm_block_unit_ht
    )

    if first_mm_M_block_idx > last_mm_M_block_idx:
        return

    tiles_to_read = how_many_tiles_to_read_formula(
        first_row_in_mm_M_block_idx,
        first_chunk_col_in_tiles,
        first_mm_M_block_idx,
        advance_by_tiles,
        last_mm_M_block_idx,
        chunk_piece_size,
        chunk_width_in_tiles
    )

    while tiles_to_read > 0:
        print(f"--------------------------------")
        print(f"tiles_to_read: {tiles_to_read}")
        tiles_to_read_in_this_step = min(tiles_to_read, tile_granularity)
        tiles_to_read -= tiles_to_read_in_this_step
        for i in range(tiles_to_read_in_this_step):
            read_tile_coords(
                i,
                first_row_in_mm_M_block_idx,
                first_chunk_col_in_tiles,
                first_mm_M_block_idx
            )
            (
                first_row_in_mm_M_block_idx,
                first_chunk_col_in_tiles,
                first_mm_M_block_idx
            ) = read_next_tile(
                first_row_in_mm_M_block_idx,
                first_chunk_col_in_tiles,
                first_mm_M_block_idx,
                advance_by_tiles,
                chunk_piece_size,
                chunk_width_in_tiles,
                mm_block_unit_ht
            )

def read_tile_coords(
    i: int,
    row_in_mm_M_block_idx: int,
    chunk_col_in_tiles: int,
    mm_M_block_idx: int
):
    """
    Read the this tile.
    """
    print(
        f"i: {i}, "
        f"row_in_mm_M_block_idx: {row_in_mm_M_block_idx}, "
        f"chunk_col_in_tiles: {chunk_col_in_tiles}, "
        f"mm_M_block_idx: {mm_M_block_idx}"
    )

if __name__ == "__main__":
    worker_id = 0
    row_in_mm_M_block_idx = 0
    chunk_col_in_tiles = 0
    mm_M_block_idx = 0
    last_mm_M_block_idx = 2
    advance_by_tiles = 2
    tile_granularity = 8

    # Config values
    mm_block_unit_ht = 2
    mm_block_unit_wt = 2
    chunk_width = 2
    chunk_width_in_tiles = chunk_width * mm_block_unit_wt
    chunk_piece_size = mm_block_unit_ht * chunk_width_in_tiles

    assert worker_id < advance_by_tiles

    read_tiles_granular(
        worker_id,
        row_in_mm_M_block_idx,
        chunk_col_in_tiles,
        mm_M_block_idx,
        advance_by_tiles,
        last_mm_M_block_idx,
        tile_granularity,
        chunk_piece_size,
        chunk_width_in_tiles,
        mm_block_unit_ht
    )



