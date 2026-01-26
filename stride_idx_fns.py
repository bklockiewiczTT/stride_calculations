from dataclasses import dataclass
import config
from config import GridConfig, reset_config
from stride_fns import read_next_tile, how_many_tiles_to_read_formula, read_tile_coords


@dataclass
class ReadTilesGranularParams:
    worker_id: int = 0
    start_row_in_mm: int = 0
    start_chunk_col: int = 0
    start_mm_M_block: int = 0
    advance_by_tiles: int = 2
    last_mm_M_block: int = 3
    tile_granularity: int = 8
    chunk_idx: int = 0


def get_effective_chunk_width_in_tiles(chunk_idx: int) -> int:
    """
    Get the effective chunk width in tiles for a given chunk index.
    If this is the last chunk in the slice and doesn't fit fully, return the remaining width.
    """
    start_col = chunk_idx * config.cfg.chunk_width_in_tiles
    end_col = min((chunk_idx + 1) * config.cfg.chunk_width_in_tiles, config.cfg.slice_Wt)
    return end_col - start_col


def read_tiles_granular_from_params(params: ReadTilesGranularParams):
    """
    Call read_tiles_granular using parameters from a ReadTilesGranularParams instance.
    """
    read_tiles_granular(
        worker_id=params.worker_id,
        start_row_in_mm=params.start_row_in_mm,
        start_chunk_col=params.start_chunk_col,
        start_mm_M_block=params.start_mm_M_block,
        advance_by_tiles=params.advance_by_tiles,
        last_mm_M_block=params.last_mm_M_block,
        tile_granularity=params.tile_granularity,
        chunk_idx=params.chunk_idx
    )

def coordinates_to_slice_coordinates(
    row_in_mm: int,
    chunk_col: int,
    mm_M_block: int,
    N_block_idx: int,
    M_block_idx: int,
    chunk_idx: int,
    N_block_wt: int):
    """
    Convert the coordinates to the slice tile index.
    """
    rows_before_this_core = mm_M_block * config.cfg.tiles_ht_per_core
    rows_before_slice = M_block_idx * config.cfg.mm_block_unit_ht
    slice_row = rows_before_this_core + rows_before_slice + row_in_mm
    slice_col = N_block_idx * N_block_wt + chunk_idx * config.cfg.chunk_width_in_tiles + chunk_col
    return slice_row, slice_col

def slice_coordinates_to_slice_tile_index(
    slice_row: int,
    slice_col: int):
    """
    Convert the slice coordinates to the tile index.
    """
    tile_index = slice_row * config.cfg.slice_Wt + slice_col
    return tile_index

def slice_coordinates_to_global_tile_index(
    slice_row: int,
    slice_col: int):
    """
    Convert the slice coordinates to the global tile index.
    """
    global_col = slice_col + config.cfg.slice_actual_idx * config.cfg.slice_Wt
    global_row = slice_row
    return global_row * config.cfg.global_Wt + global_col

def read_tiles_granular(
    worker_id: int,
    start_row_in_mm: int,
    start_chunk_col: int,
    start_mm_M_block: int,
    advance_by_tiles: int,
    last_mm_M_block: int,
    tile_granularity: int,
    chunk_idx: int
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

    # Compute effective chunk dimensions for stride_fns
    effective_chunk_width_in_tiles = get_effective_chunk_width_in_tiles(chunk_idx)
    effective_chunk_piece_size = config.cfg.mm_block_unit_ht * effective_chunk_width_in_tiles

    first_row_in_mm, first_chunk_col, first_mm_M_block = read_next_tile(start_row_in_mm, start_chunk_col, start_mm_M_block, worker_id, effective_chunk_piece_size, effective_chunk_width_in_tiles, config.cfg.mm_block_unit_ht)
    if first_mm_M_block > last_mm_M_block:
        return
    tiles_to_read = how_many_tiles_to_read_formula(first_row_in_mm, first_chunk_col, first_mm_M_block, advance_by_tiles, last_mm_M_block, effective_chunk_piece_size, effective_chunk_width_in_tiles)
    while tiles_to_read > 0:
        print(f"--------------------------------")
        print(f"tiles_to_read: {tiles_to_read}")
        tiles_to_read_in_this_step = min(tiles_to_read, tile_granularity)
        tiles_to_read -= tiles_to_read_in_this_step
        for i in range(tiles_to_read_in_this_step):
            slice_row, slice_col = coordinates_to_slice_coordinates(first_row_in_mm, first_chunk_col, first_mm_M_block, config.cfg.N_block_idx, config.cfg.M_block_idx, chunk_idx, config.cfg.N_block_wt)
            # read_tile_coords(i, first_row_in_mm, first_chunk_col, first_mm_M_block)
            # print(f"slice_row: {slice_row}, slice_col: {slice_col}")
            first_row_in_mm, first_chunk_col, first_mm_M_block = read_next_tile(first_row_in_mm, first_chunk_col, first_mm_M_block, advance_by_tiles, effective_chunk_piece_size, effective_chunk_width_in_tiles, config.cfg.mm_block_unit_ht)
            slice_tile_idx = slice_coordinates_to_slice_tile_index(slice_row, slice_col)
            global_tile_idx = slice_coordinates_to_global_tile_index(slice_row, slice_col)
            print(f"slice_tile_idx: {slice_tile_idx}, global_tile_idx: {global_tile_idx}")


if __name__ == "__main__":
    # Reset config with custom values
    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=4,
    #     chunk_width=2,
    #     mm_block_unit_ht=2,
    #     mm_M_unit_blocks_per_core=4,
    #     mm_N_blocks_per_slice=2,
    #     ring_size=2,
    #     N_block_idx=0,
    #     M_block_idx=0,
    #     slice_actual_idx=0,
    # ))
    # config.cfg.print_config()

    # params = ReadTilesGranularParams(
    #     worker_id=1,
    #     start_row_in_mm=0,
    #     start_chunk_col=0,
    #     start_mm_M_block=0,
    #     advance_by_tiles=3,
    #     last_mm_M_block=3,
    #     tile_granularity=5
    # )
    # read_tiles_granular_from_params(params)

    reset_config(GridConfig(
        mm_block_unit_wt=2,
        mm_blocks_per_N_block=4,
        chunk_width=2,
        mm_block_unit_ht=2,
        mm_M_unit_blocks_per_core=4,
        mm_N_blocks_per_slice=2,
        ring_size=2,
        N_block_idx=0,
        M_block_idx=0,
        slice_actual_idx=0,
    ))
    config.cfg.print_config()

    params = ReadTilesGranularParams(
        worker_id=0,
        start_row_in_mm=0,
        start_chunk_col=0,
        start_mm_M_block=0,
        advance_by_tiles=1,
        last_mm_M_block=3,
        tile_granularity=5,
        chunk_idx=0
    )
    read_tiles_granular_from_params(params)