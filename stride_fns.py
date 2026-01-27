# chunk is a 2D array of 1 x chunk_width units so mm_block_unit_ht by chunk_width * mm_block_unit_wt tiles

def read_next_tile(
    row_in_mm: int,
    chunk_col: int,
    mm_M_block: int,
    advance_by_tiles: int,
    chunk_piece_size: int,
    chunk_width_in_tiles: int,
    mm_block_unit_ht: int) -> tuple[int, int, int]:
    """
    Read the next tile from the chunk.
    """
    if advance_by_tiles < 0:
        raise ValueError("advance_by_tiles must be greater than 0")
    if advance_by_tiles == 0:
        return row_in_mm, chunk_col, mm_M_block

    # TODO: this can be simplified by using the modulo operator
    if advance_by_tiles >= chunk_piece_size:
        move_by_pieces = advance_by_tiles // chunk_piece_size
        advance_by_tiles -= move_by_pieces * chunk_piece_size
        mm_M_block += move_by_pieces

    # TODO: this can be simplified by using the modulo operator
    if advance_by_tiles >= chunk_width_in_tiles:
        move_by_rows = advance_by_tiles // chunk_width_in_tiles
        new_row = row_in_mm + move_by_rows
        advance_by_tiles -= move_by_rows * chunk_width_in_tiles
        if (new_row >= mm_block_unit_ht):
            mm_M_block += 1
            row_in_mm = new_row % mm_block_unit_ht
        else:
            row_in_mm = new_row
    
    new_col = chunk_col + advance_by_tiles
    if (new_col >= chunk_width_in_tiles):
        row_in_mm += 1
        if (row_in_mm >= mm_block_unit_ht):
            mm_M_block += 1
            row_in_mm = 0
        new_col = new_col % chunk_width_in_tiles
    
    # print(f"advance_by_tiles: {advance_by_tiles}")
    # print(f"row_in_mm: {row_in_mm}, new_col: {new_col}, mm_M_block: {mm_M_block}")
    
    return row_in_mm, new_col, mm_M_block

def how_many_tiles_to_read_formula(
    row_in_mm: int,
    chunk_col: int,
    mm_M_block: int,
    advance_by_tiles: int,
    last_mm_M_block: int,
    chunk_piece_size: int,
    chunk_width_in_tiles: int):
    
    current_block_tiles_remaining = chunk_piece_size - (row_in_mm * chunk_width_in_tiles + chunk_col) - 1
    future_blocks_tiles = (last_mm_M_block - mm_M_block) * chunk_piece_size
    all_tiles = current_block_tiles_remaining + future_blocks_tiles
    return 1 + all_tiles // advance_by_tiles

def read_tiles_granular(
    worker_id: int,
    start_row_in_mm: int,
    start_chunk_col: int,
    start_mm_M_block: int,
    advance_by_tiles: int,
    last_mm_M_block: int,
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
    if last_mm_M_block < start_mm_M_block:
        raise ValueError("last_mm_M_block must be greater than or equal to start_mm_M_block")

    first_row_in_mm, first_chunk_col, first_mm_M_block = read_next_tile(start_row_in_mm, start_chunk_col, start_mm_M_block, worker_id, chunk_piece_size, chunk_width_in_tiles, mm_block_unit_ht)
    if first_mm_M_block > last_mm_M_block:
        return
    tiles_to_read = how_many_tiles_to_read_formula(first_row_in_mm, first_chunk_col, first_mm_M_block, advance_by_tiles, last_mm_M_block, chunk_piece_size, chunk_width_in_tiles)
    while tiles_to_read > 0:
        print(f"--------------------------------")
        print(f"tiles_to_read: {tiles_to_read}")
        tiles_to_read_in_this_step = min(tiles_to_read, tile_granularity)
        tiles_to_read -= tiles_to_read_in_this_step
        for i in range(tiles_to_read_in_this_step):
            read_tile_coords(i, first_row_in_mm, first_chunk_col, first_mm_M_block)
            first_row_in_mm, first_chunk_col, first_mm_M_block = read_next_tile(first_row_in_mm, first_chunk_col, first_mm_M_block, advance_by_tiles, chunk_piece_size, chunk_width_in_tiles, mm_block_unit_ht)

def read_tile_coords(
    i : int,
    row_in_mm: int,
    chunk_col: int,
    mm_M_block: int):
    """
    Read the this tile.
    """
    print(f"i: {i}, row_in_mm: {row_in_mm}, chunk_col: {chunk_col}, mm_M_block: {mm_M_block}")

if __name__ == "__main__":
    worker_id = 0
    row_in_mm = 0
    chunk_col = 0
    mm_M_block = 0
    last_mm_M_block = 2
    advance_by_tiles = 2
    tile_granularity = 8

    # Config values
    mm_block_unit_ht = 2
    mm_block_unit_wt = 2
    chunk_width = 2
    chunk_width_in_tiles = chunk_width * mm_block_unit_wt
    chunk_piece_size = mm_block_unit_ht * chunk_width_in_tiles

    assert worker_id < advance_by_tiles

    read_tiles_granular(worker_id, row_in_mm, chunk_col, mm_M_block, advance_by_tiles, last_mm_M_block, tile_granularity, chunk_piece_size, chunk_width_in_tiles, mm_block_unit_ht)



