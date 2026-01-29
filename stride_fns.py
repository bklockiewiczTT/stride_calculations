# chunk is a 2D array of mm_unit x chunk_width_in_mm_units units
# so mm_block_unit_ht by chunk_width_in_mm_units * mm_block_unit_wt tiles

def get_next_tile_coordinates(
    tile_row_in_mm_M_block: int,
    chunk_col_in_tiles: int,
    mm_core_idx: int,
    advance_by_tiles: int,
    chunk_piece_size: int,
    chunk_width_in_tiles: int,
    mm_block_unit_ht: int
) -> tuple[int, int, int]:
    """
    Read the next tile from the chunk.
    """
    assert chunk_piece_size == mm_block_unit_ht * chunk_width_in_tiles
    assert tile_row_in_mm_M_block < mm_block_unit_ht
    assert chunk_col_in_tiles < chunk_width_in_tiles
    assert mm_core_idx >= 0
    assert tile_row_in_mm_M_block >= 0
    assert advance_by_tiles >= 0

    if advance_by_tiles < 0:
        raise ValueError("advance_by_tiles must be greater than 0")
    if advance_by_tiles == 0:
        return tile_row_in_mm_M_block, chunk_col_in_tiles, mm_core_idx

    if advance_by_tiles >= chunk_piece_size:
        move_by_pieces = advance_by_tiles // chunk_piece_size
        advance_by_tiles -= move_by_pieces * chunk_piece_size
        mm_core_idx += move_by_pieces

    if advance_by_tiles >= chunk_width_in_tiles:
        move_by_rows = advance_by_tiles // chunk_width_in_tiles
        new_row = tile_row_in_mm_M_block + move_by_rows
        advance_by_tiles -= move_by_rows * chunk_width_in_tiles
        if new_row >= mm_block_unit_ht:
            mm_core_idx += 1
            tile_row_in_mm_M_block = new_row % mm_block_unit_ht
        else:
            tile_row_in_mm_M_block = new_row

    new_col = chunk_col_in_tiles + advance_by_tiles
    if new_col >= chunk_width_in_tiles:
        tile_row_in_mm_M_block += 1
        if tile_row_in_mm_M_block >= mm_block_unit_ht:
            mm_core_idx += 1
            tile_row_in_mm_M_block = 0
        new_col = new_col % chunk_width_in_tiles

    return tile_row_in_mm_M_block, new_col, mm_core_idx

def get_next_tile_coordinates_optimized(
    tile_row_in_mm_M_block: int,
    chunk_col_in_tiles: int,
    mm_core_idx: int,
    advance_by_tiles: int,
    chunk_piece_size: int,
    chunk_width_in_tiles: int,
    mm_block_unit_ht: int
) -> tuple[int, int, int]:
    """
    Read the next tile from the chunk.
    
    Optimized to avoid divisions when advance_by_tiles < chunk_width_in_tiles.
    """
    assert chunk_piece_size == mm_block_unit_ht * chunk_width_in_tiles
    assert tile_row_in_mm_M_block < mm_block_unit_ht
    assert chunk_col_in_tiles < chunk_width_in_tiles
    assert mm_core_idx >= 0
    assert tile_row_in_mm_M_block >= 0
    assert advance_by_tiles >= 0

    # 1. Check for "Piece" Jump - SKIPS EXPENSIVE MATH when advance is small
    if advance_by_tiles >= chunk_width_in_tiles:
        if advance_by_tiles >= chunk_piece_size:
            move_by_pieces = advance_by_tiles // chunk_piece_size
            advance_by_tiles -= move_by_pieces * chunk_piece_size
            mm_core_idx += move_by_pieces

        # 2. Check for "Row" Jump
        if advance_by_tiles >= chunk_width_in_tiles:
            move_by_rows = advance_by_tiles // chunk_width_in_tiles
            new_row = tile_row_in_mm_M_block + move_by_rows
            advance_by_tiles -= move_by_rows * chunk_width_in_tiles
            
            if new_row >= mm_block_unit_ht:
                mm_core_idx += (new_row // mm_block_unit_ht)
                tile_row_in_mm_M_block = new_row % mm_block_unit_ht
            else:
                tile_row_in_mm_M_block = new_row

    # 3. Handle Remaining Columns - FAST ADDITION
    new_col = chunk_col_in_tiles + advance_by_tiles
    
    if new_col >= chunk_width_in_tiles:
        tile_row_in_mm_M_block += 1
        new_col -= chunk_width_in_tiles
        if tile_row_in_mm_M_block >= mm_block_unit_ht:
            mm_core_idx += 1
            tile_row_in_mm_M_block = 0

    return tile_row_in_mm_M_block, new_col, mm_core_idx

def get_next_tile_coordinates_2(
    tile_row_in_mm_M_block: int,
    chunk_col_in_tiles: int,
    mm_core_idx: int,
    advance_by_tiles: int,
    chunk_width_in_tiles: int,
    mm_block_unit_ht: int
):
    """
    Read the next tile from the chunk.
    """
    if advance_by_tiles < 0:
        raise ValueError("advance_by_tiles must be greater than 0")
    if advance_by_tiles == 0:
        return tile_row_in_mm_M_block, chunk_col_in_tiles, mm_core_idx
    
    assert tile_row_in_mm_M_block < mm_block_unit_ht
    assert chunk_col_in_tiles < chunk_width_in_tiles
    assert mm_core_idx >= 0
    assert tile_row_in_mm_M_block >= 0
    assert advance_by_tiles >= 0

    chunk_piece_size = mm_block_unit_ht * chunk_width_in_tiles

    move_by_pieces = advance_by_tiles // chunk_piece_size
    advance_by_tiles -= move_by_pieces * chunk_piece_size
    mm_core_idx += move_by_pieces

    move_by_rows = advance_by_tiles // chunk_width_in_tiles
    new_row = tile_row_in_mm_M_block + move_by_rows
    advance_by_tiles -= move_by_rows * chunk_width_in_tiles
    mm_core_idx += (new_row // mm_block_unit_ht)
    tile_row_in_mm_M_block = new_row % mm_block_unit_ht

    new_col = chunk_col_in_tiles + advance_by_tiles
    tile_row_in_mm_M_block += new_col // chunk_width_in_tiles
    mm_core_idx += (tile_row_in_mm_M_block // mm_block_unit_ht)
    tile_row_in_mm_M_block = tile_row_in_mm_M_block % mm_block_unit_ht
    new_col = new_col % chunk_width_in_tiles

    return tile_row_in_mm_M_block, new_col, mm_core_idx

def get_next_tile_coordinates_flat(
    tile_row_in_mm_M_block: int,
    chunk_col_in_tiles: int,
    mm_core_idx: int,
    advance_by_tiles: int,
    chunk_width_in_tiles: int,
    mm_block_unit_ht: int
):
    """
    Read the next tile from the chunk using a flattened index approach.
    """
    if advance_by_tiles < 0:
        raise ValueError("advance_by_tiles must be greater than 0")

    chunk_piece_size = mm_block_unit_ht * chunk_width_in_tiles
    current_chunk_index = (
        (mm_core_idx * chunk_piece_size) + 
        (tile_row_in_mm_M_block * chunk_width_in_tiles) + 
        chunk_col_in_tiles
    )
    target_chunk_index = current_chunk_index + advance_by_tiles
    mm_core_idx = target_chunk_index // chunk_piece_size
    remaining_tiles = target_chunk_index % chunk_piece_size
    
    tile_row_in_mm_M_block = remaining_tiles // chunk_width_in_tiles
    chunk_col_in_tiles = remaining_tiles % chunk_width_in_tiles

    return tile_row_in_mm_M_block, chunk_col_in_tiles, mm_core_idx

def how_many_tiles_to_read_formula(
    tile_row_in_mm_M_block: int,
    chunk_col_in_tiles: int,
    mm_core_idx: int,
    advance_by_tiles: int,
    last_mm_core_idx: int,
    chunk_piece_size: int,
    chunk_width_in_tiles: int
):
    current_tile_offset = (
        tile_row_in_mm_M_block * chunk_width_in_tiles + chunk_col_in_tiles
    )
    current_block_tiles_remaining = chunk_piece_size - current_tile_offset - 1
    future_blocks_tiles = (
        (last_mm_core_idx - mm_core_idx) * chunk_piece_size
    )
    all_tiles = current_block_tiles_remaining + future_blocks_tiles
    return 1 + all_tiles // advance_by_tiles

def read_tiles_granular(
    worker_id: int,
    start_tile_row_in_mm_M_block: int,
    start_chunk_col_in_tiles: int,
    start_mm_core_idx: int,
    advance_by_tiles: int,
    last_mm_core_idx: int,
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
    if last_mm_core_idx < start_mm_core_idx:
        raise ValueError(
            "last_mm_core_idx must be >= start_mm_core_idx"
        )

    (
        first_tile_row_in_mm_M_block,
        first_chunk_col_in_tiles,
        first_mm_core_idx
    ) = get_next_tile_coordinates_optimized(
        start_tile_row_in_mm_M_block,
        start_chunk_col_in_tiles,
        start_mm_core_idx,
        worker_id,
        chunk_piece_size,
        chunk_width_in_tiles,
        mm_block_unit_ht
    )

    if first_mm_core_idx > last_mm_core_idx:
        return

    tiles_to_read = how_many_tiles_to_read_formula(
        first_tile_row_in_mm_M_block,
        first_chunk_col_in_tiles,
        first_mm_core_idx,
        advance_by_tiles,
        last_mm_core_idx,
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
                first_tile_row_in_mm_M_block,
                first_chunk_col_in_tiles,
                first_mm_core_idx
            )
            (
                first_tile_row_in_mm_M_block,
                first_chunk_col_in_tiles,
                first_mm_core_idx
            ) = get_next_tile_coordinates_optimized(
                first_tile_row_in_mm_M_block,
                first_chunk_col_in_tiles,
                first_mm_core_idx,
                advance_by_tiles,
                chunk_piece_size,
                chunk_width_in_tiles,
                mm_block_unit_ht
            )

def read_tile_coords(
    i: int,
    tile_row_in_mm_M_block: int,
    chunk_col_in_tiles: int,
    mm_core_idx: int
):
    """
    Read the this tile.
    """
    print(
        f"i: {i}, "
        f"tile_row_in_mm_M_block: {tile_row_in_mm_M_block}, "
        f"chunk_col_in_tiles: {chunk_col_in_tiles}, "
        f"mm_core_idx: {mm_core_idx}"
    )

if __name__ == "__main__":
    worker_id = 0
    tile_row_in_mm_M_block = 0
    chunk_col_in_tiles = 0
    mm_core_idx = 0
    last_mm_core_idx = 2
    advance_by_tiles = 2
    tile_granularity = 8

    # Config values
    mm_block_unit_ht = 2
    mm_block_unit_wt = 2
    chunk_width_in_mm_units = 2
    chunk_width_in_tiles = chunk_width_in_mm_units * mm_block_unit_wt
    chunk_piece_size = mm_block_unit_ht * chunk_width_in_tiles

    assert worker_id < advance_by_tiles

    read_tiles_granular(
        worker_id,
        tile_row_in_mm_M_block,
        chunk_col_in_tiles,
        mm_core_idx,
        advance_by_tiles,
        last_mm_core_idx,
        tile_granularity,
        chunk_piece_size,
        chunk_width_in_tiles,
        mm_block_unit_ht
    )



