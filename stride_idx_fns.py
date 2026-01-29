from dataclasses import dataclass
import config
from config import GridConfig, reset_config
from stride_fns import get_next_tile_coordinates_optimized, how_many_tiles_to_read_formula


@dataclass
class ReadTilesGranularParams:
    worker_id: int = 0
    start_tile_row_in_mm_M_block: int = 0
    start_chunk_col_in_tiles: int = 0
    start_mm_core_idx: int = 0
    advance_by_tiles: int = 2
    last_mm_core_idx: int = 3
    tile_granularity: int = 8
    chunk_idx: int = 0
    direction: int = 1
    num_workers: int = 2

def get_effective_chunk_width_in_tiles(chunk_idx: int) -> int:
    """
    Get the effective chunk width in tiles for a given chunk index.
    If this is the last chunk in the slice and doesn't fit fully, return the remaining width.
    """
    start_col = chunk_idx * config.cfg.chunk_width_in_tiles
    remaining_width = config.cfg.N_block_wt - start_col
    # print(f"remaining width: {remaining_width}")
    return min(remaining_width, config.cfg.chunk_width_in_tiles)

def read_tiles_granular_from_params(
    params: ReadTilesGranularParams
) -> tuple[list[int], list[int]]:
    """
    Call read_tiles_granular using parameters from a ReadTilesGranularParams instance.
    """
    return read_tiles_granular(
        worker_id=params.worker_id,
        start_tile_row_in_mm_M_block=params.start_tile_row_in_mm_M_block,
        start_chunk_col_in_tiles=params.start_chunk_col_in_tiles,
        start_mm_core_idx=params.start_mm_core_idx,
        advance_by_tiles=params.advance_by_tiles,
        last_mm_core_idx=params.last_mm_core_idx,
        tile_granularity=params.tile_granularity,
        chunk_idx=params.chunk_idx
    )

def read_tiles_granular_from_params_with_direction(
    params: ReadTilesGranularParams
) -> tuple[list[int], list[int]]:
    """
    Call read_tiles_granular using parameters from a ReadTilesGranularParams instance.
    """
    return read_tiles_granular_with_direction(
        worker_id=params.worker_id,
        start_tile_row_in_mm_M_block=params.start_tile_row_in_mm_M_block,
        start_chunk_col_in_tiles=params.start_chunk_col_in_tiles,
        start_mm_core_idx=params.start_mm_core_idx,
        advance_by_tiles=params.advance_by_tiles,
        last_mm_core_idx=params.last_mm_core_idx,
        tile_granularity=params.tile_granularity,
        chunk_idx=params.chunk_idx,
        direction=params.direction
    )

def read_tiles_granular_with_direction_based_on_num_workers_from_params(
    params: ReadTilesGranularParams
) -> tuple[list[list[int]], list[list[int]]]:
    """
    Call read_tiles_granular_with_direction_based_on_num_workers using parameters from a ReadTilesGranularParams instance.
    """
    return read_tiles_granular_with_direction_based_on_num_workers(
        worker_id=params.worker_id,
        start_tile_row_in_mm_M_block=params.start_tile_row_in_mm_M_block,
        start_chunk_col_in_tiles=params.start_chunk_col_in_tiles,
        start_mm_core_idx=params.start_mm_core_idx,
        last_mm_core_idx=params.last_mm_core_idx,
        tile_granularity=params.tile_granularity,
        chunk_idx=params.chunk_idx,
        direction=params.direction,
        num_workers=params.num_workers
    )

def coordinates_to_slice_coordinates(
    tile_row_in_mm_M_block: int,
    chunk_col_in_tiles: int,
    mm_core_idx: int,
    N_block_idx: int,
    M_block_idx: int,
    chunk_idx: int,
    N_block_wt: int):
    """
    Convert the coordinates to the slice tile index.
    """
    rows_before_this_core = mm_core_idx * config.cfg.tiles_ht_per_core
    rows_before_piece = M_block_idx * config.cfg.mm_block_unit_ht
    slice_row = rows_before_this_core + rows_before_piece + tile_row_in_mm_M_block
    slice_col = (N_block_idx * N_block_wt +
                 chunk_idx * config.cfg.chunk_width_in_tiles +
                 chunk_col_in_tiles)
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
    # print(f"slice_col: {slice_col}, slice_actual_idx: {config.cfg.slice_actual_idx}, "
    #       f"slice_Wt: {config.cfg.slice_Wt}")
    global_col = slice_col + config.cfg.slice_actual_idx * config.cfg.slice_Wt
    global_row = slice_row
    return global_row * config.cfg.global_Wt + global_col

def read_tiles_granular(
    worker_id: int,
    start_tile_row_in_mm_M_block: int,
    start_chunk_col_in_tiles: int,
    start_mm_core_idx: int,
    advance_by_tiles: int,
    last_mm_core_idx: int,
    tile_granularity: int,
    chunk_idx: int
    ) -> tuple[list[list[int]], list[list[int]]]:
    """
    Read the tiles granularly.
    Returns lists of lists where each sublist corresponds to one iteration of the outer while loop.
    """
    if tile_granularity <= 0:
        raise ValueError("tile_granularity must be greater than 0")
    if advance_by_tiles <= 0:
        raise ValueError("advance_by_tiles must be greater than 0")
    if last_mm_core_idx < start_mm_core_idx:
        raise ValueError(
            "last_mm_core_idx must be greater than or equal to start_mm_core_idx"
        )
    
    slice_idxs = []
    global_idxs = []

    # Compute effective chunk dimensions for stride_fns
    effective_chunk_width_in_tiles = get_effective_chunk_width_in_tiles(chunk_idx)
    effective_chunk_piece_size = (config.cfg.mm_block_unit_ht *
                                  effective_chunk_width_in_tiles)

    (first_tile_row_in_mm_M_block,
     first_chunk_col_in_tiles,
     first_mm_core_idx) = get_next_tile_coordinates_optimized(
        start_tile_row_in_mm_M_block, start_chunk_col_in_tiles, start_mm_core_idx,
        worker_id, effective_chunk_piece_size, effective_chunk_width_in_tiles,
        config.cfg.mm_block_unit_ht
    )
    if first_mm_core_idx > last_mm_core_idx:
        return [], []
    tiles_to_read = how_many_tiles_to_read_formula(
        first_tile_row_in_mm_M_block, first_chunk_col_in_tiles, first_mm_core_idx,
        advance_by_tiles, last_mm_core_idx,
        effective_chunk_piece_size, effective_chunk_width_in_tiles
    )
    while tiles_to_read > 0:
        print(f"--------------------------------")
        print(f"tiles_to_read: {tiles_to_read}")
        tiles_to_read_in_this_step = min(tiles_to_read, tile_granularity)
        tiles_to_read -= tiles_to_read_in_this_step
        step_slice_idxs = []
        step_global_idxs = []
        for i in range(tiles_to_read_in_this_step):
            slice_row, slice_col = coordinates_to_slice_coordinates(
                first_tile_row_in_mm_M_block, first_chunk_col_in_tiles,
                first_mm_core_idx, config.cfg.N_block_idx, config.cfg.M_block_idx,
                chunk_idx, config.cfg.N_block_wt
            )
            # read_tile_coords(i, first_tile_row_in_mm_M_block,
            #                  first_chunk_col_in_tiles, first_mm_core_idx)
            # print(f"slice_row: {slice_row}, slice_col: {slice_col}")
            (first_tile_row_in_mm_M_block,
             first_chunk_col_in_tiles,
             first_mm_core_idx) = get_next_tile_coordinates_optimized(
                first_tile_row_in_mm_M_block, first_chunk_col_in_tiles,
                first_mm_core_idx, advance_by_tiles, effective_chunk_piece_size,
                effective_chunk_width_in_tiles, config.cfg.mm_block_unit_ht
            )
            slice_tile_idx = slice_coordinates_to_slice_tile_index(slice_row, slice_col)
            global_tile_idx = slice_coordinates_to_global_tile_index(slice_row, slice_col)
            step_slice_idxs.append(slice_tile_idx)
            step_global_idxs.append(global_tile_idx)
            print(f"slice_tile_idx: {slice_tile_idx}, global_tile_idx: {global_tile_idx}")
        slice_idxs.append(step_slice_idxs)
        global_idxs.append(step_global_idxs)
    return slice_idxs, global_idxs


def read_tiles_granular_with_direction(
    worker_id: int,
    start_tile_row_in_mm_M_block: int,
    start_chunk_col_in_tiles: int,
    start_mm_core_idx: int,
    advance_by_tiles: int,
    last_mm_core_idx: int,
    tile_granularity: int,
    chunk_idx: int,
    direction: int) -> tuple[list[list[int]], list[list[int]]]:
    """
    Read the tiles granularly.
    Returns lists of lists where each sublist corresponds to one iteration of the outer while loop.
    """
    if tile_granularity <= 0:
        raise ValueError("tile_granularity must be greater than 0")
    if advance_by_tiles <= 0:
        raise ValueError("advance_by_tiles must be greater than 0")
    if last_mm_core_idx < start_mm_core_idx:
        raise ValueError(
            "last_mm_core_idx must be greater than or equal to start_mm_core_idx"
        )

    # Compute effective chunk dimensions for stride_fns
    effective_chunk_width_in_tiles = get_effective_chunk_width_in_tiles(chunk_idx)
    effective_chunk_piece_size = (config.cfg.mm_block_unit_ht *
                                  effective_chunk_width_in_tiles)
    slice_idxs = []
    global_idxs = []

    (first_tile_row_in_mm_M_block,
     first_chunk_col_in_tiles,
     first_mm_core_idx) = get_next_tile_coordinates_optimized(
        start_tile_row_in_mm_M_block, start_chunk_col_in_tiles, start_mm_core_idx,
        worker_id, effective_chunk_piece_size, effective_chunk_width_in_tiles,
        config.cfg.mm_block_unit_ht
    )
    if first_mm_core_idx > last_mm_core_idx:
        return slice_idxs, global_idxs
    tiles_to_read = how_many_tiles_to_read_formula(
        first_tile_row_in_mm_M_block, first_chunk_col_in_tiles, first_mm_core_idx,
        advance_by_tiles, last_mm_core_idx,
        effective_chunk_piece_size, effective_chunk_width_in_tiles
    )
    
    tiles_to_read_forward = (tiles_to_read + 1) // 2
    tiles_to_read_backward = tiles_to_read - tiles_to_read_forward
    tiles_to_read = tiles_to_read_forward if direction == 0 else tiles_to_read_backward
    oddity_bool = True

    while tiles_to_read > 0:
        print(f"--------------------------------")
        print(f"tiles_to_read: {tiles_to_read}")
        tiles_to_read_in_this_step = min(tiles_to_read, tile_granularity)
        tiles_read = 0
        step_slice_idxs = []
        step_global_idxs = []
        while tiles_read < tiles_to_read_in_this_step:
            # print(f"oddity_bool: {oddity_bool}")
            # print(f"direction: {direction}")
            # print(f"reading tile")
            slice_row, slice_col = coordinates_to_slice_coordinates(
                first_tile_row_in_mm_M_block, first_chunk_col_in_tiles,
                first_mm_core_idx, config.cfg.N_block_idx, config.cfg.M_block_idx,
                chunk_idx, config.cfg.N_block_wt
            )
            # read_tile_coords(i, first_tile_row_in_mm_M_block,
            #                  first_chunk_col_in_tiles, first_mm_core_idx)
            (first_tile_row_in_mm_M_block,
             first_chunk_col_in_tiles,
             first_mm_core_idx) = get_next_tile_coordinates_optimized(
                first_tile_row_in_mm_M_block, first_chunk_col_in_tiles,
                first_mm_core_idx, advance_by_tiles, effective_chunk_piece_size,
                effective_chunk_width_in_tiles, config.cfg.mm_block_unit_ht
            )

            if oddity_bool == (direction == 0):
                slice_tile_idx = slice_coordinates_to_slice_tile_index(slice_row, slice_col)
                global_tile_idx = slice_coordinates_to_global_tile_index(slice_row, slice_col)
                print(f"slice_row: {slice_row}, slice_col: {slice_col}") 
                # print(f"slice_tile_idx: {slice_tile_idx}, global_tile_idx: {global_tile_idx}")
                tiles_read += 1
                step_slice_idxs.append(slice_tile_idx)
                step_global_idxs.append(global_tile_idx)
            oddity_bool = not oddity_bool
        slice_idxs.append(step_slice_idxs)
        global_idxs.append(step_global_idxs)
        tiles_to_read -= tiles_to_read_in_this_step
    return slice_idxs, global_idxs


def read_tiles_granular_with_direction_based_on_num_workers(
    worker_id: int,
    start_tile_row_in_mm_M_block: int,
    start_chunk_col_in_tiles: int,
    start_mm_core_idx: int,
    last_mm_core_idx: int,
    tile_granularity: int,
    chunk_idx: int,
    direction: int,
    num_workers: int) -> tuple[list[list[int]], list[list[int]]]:
    """
    Read the tiles granularly.
    Returns lists of lists where each sublist corresponds to one iteration of the outer while loop.
    """
    if tile_granularity <= 0:
        raise ValueError("tile_granularity must be greater than 0")
    if last_mm_core_idx < start_mm_core_idx:
        raise ValueError(
            "last_mm_core_idx must be greater than or equal to start_mm_core_idx"
        )
    if num_workers <= 0:
        raise ValueError("num_workers must be greater than 0")
    if direction not in [0, 1]:
        raise ValueError("direction must be 0 or 1")

    slice_idxs = []
    global_idxs = []

    effective_id = worker_id + direction * num_workers
    effective_advance_by_tiles = 2 * num_workers

    # Compute effective chunk dimensions for stride_fns
    effective_chunk_width_in_tiles = get_effective_chunk_width_in_tiles(chunk_idx)
    effective_chunk_piece_size = (config.cfg.mm_block_unit_ht *
                                  effective_chunk_width_in_tiles)

    (first_tile_row_in_mm_M_block,
     first_chunk_col_in_tiles,
     first_mm_core_idx) = get_next_tile_coordinates_optimized(
        start_tile_row_in_mm_M_block, start_chunk_col_in_tiles, start_mm_core_idx,
        effective_id, effective_chunk_piece_size, effective_chunk_width_in_tiles,
        config.cfg.mm_block_unit_ht
    )
    if first_mm_core_idx > last_mm_core_idx:
        return [], []
    tiles_to_read = how_many_tiles_to_read_formula(
        first_tile_row_in_mm_M_block, first_chunk_col_in_tiles, first_mm_core_idx,
        effective_advance_by_tiles, last_mm_core_idx,
        effective_chunk_piece_size, effective_chunk_width_in_tiles
    )
    while tiles_to_read > 0:
        print(f"--------------------------------")
        print(f"tiles_to_read: {tiles_to_read}")
        tiles_to_read_in_this_step = min(tiles_to_read, tile_granularity)
        tiles_to_read -= tiles_to_read_in_this_step
        step_slice_idxs = []
        step_global_idxs = []
        for i in range(tiles_to_read_in_this_step):
            slice_row, slice_col = coordinates_to_slice_coordinates(
                first_tile_row_in_mm_M_block, first_chunk_col_in_tiles,
                first_mm_core_idx, config.cfg.N_block_idx, config.cfg.M_block_idx,
                chunk_idx, config.cfg.N_block_wt
            )
            # read_tile_coords(i, first_tile_row_in_mm_M_block,
            #                  first_chunk_col_in_tiles, first_mm_core_idx)
            # print(f"slice_row: {slice_row}, slice_col: {slice_col}")
            (first_tile_row_in_mm_M_block,
             first_chunk_col_in_tiles,
             first_mm_core_idx) = get_next_tile_coordinates_optimized(
                first_tile_row_in_mm_M_block, first_chunk_col_in_tiles,
                first_mm_core_idx, effective_advance_by_tiles,
                effective_chunk_piece_size, effective_chunk_width_in_tiles,
                config.cfg.mm_block_unit_ht
            )
            slice_tile_idx = slice_coordinates_to_slice_tile_index(slice_row, slice_col)
            global_tile_idx = slice_coordinates_to_global_tile_index(slice_row, slice_col)
            step_slice_idxs.append(slice_tile_idx)
            step_global_idxs.append(global_tile_idx)
            print(f"slice_tile_idx: {slice_tile_idx}, global_tile_idx: {global_tile_idx}")
        slice_idxs.append(step_slice_idxs)
        global_idxs.append(step_global_idxs)
    return slice_idxs, global_idxs


if __name__ == "__main__":
    # Reset config with custom values
    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=4,
    #     chunk_width_in_mm_units=2,
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
    #     worker_id=0,
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     advance_by_tiles=2,
    #     last_mm_core_idx=3,
    #     tile_granularity=4
    # )
    # slice_idxs, global_idxs = read_tiles_granular_from_params(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")

    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=4,
    #     chunk_width_in_mm_units=2,
    #     mm_block_unit_ht=2,
    #     mm_M_unit_blocks_per_core=4,
    #     mm_N_blocks_per_slice=2,
    #     ring_size=2,
    #     N_block_idx=0,
    #     M_block_idx=0,
    #     slice_actual_idx=1,
    # ))
    # config.cfg.print_config()
    # params = ReadTilesGranularParams(
    #     worker_id=0,
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     advance_by_tiles=3,
    #     last_mm_core_idx=2,
    #     tile_granularity=5,
    #     chunk_idx=0
    # )
    # slice_idxs, global_idxs = read_tiles_granular_from_params(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")

    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=4,
    #     chunk_width_in_mm_units=3,
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
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     advance_by_tiles=2,
    #     last_mm_core_idx=3,
    #     tile_granularity=5,
    #     chunk_idx=1
    # )
    # slice_idxs, global_idxs = read_tiles_granular_from_params(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")


    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=4,
    #     chunk_width_in_mm_units=3,
    #     mm_block_unit_ht=2,
    #     mm_M_unit_blocks_per_core=4,
    #     mm_N_blocks_per_slice=2,
    #     ring_size=2,
    #     N_block_idx=0,
    #     M_block_idx=1,
    #     slice_actual_idx=0,
    # ))
    # config.cfg.print_config()
    # params = ReadTilesGranularParams(
    #     worker_id=0,
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     advance_by_tiles=3,
    #     last_mm_core_idx=3,
    #     tile_granularity=4,
    #     chunk_idx=0
    # )
    # slice_idxs, global_idxs = read_tiles_granular_from_params(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")

    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=4,
    #     chunk_width_in_mm_units=2,
    #     mm_block_unit_ht=2,
    #     mm_M_unit_blocks_per_core=4,
    #     mm_N_blocks_per_slice=2,
    #     ring_size=2,
    #     N_block_idx=1,
    #     M_block_idx=2,
    #     slice_actual_idx=0,
    # ))
    # config.cfg.print_config()
    # params = ReadTilesGranularParams(
    #     worker_id=0,
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     advance_by_tiles=3,
    #     last_mm_core_idx=3,
    #     tile_granularity=5,
    #     chunk_idx=1
    # )
    # slice_idxs, global_idxs = read_tiles_granular_from_params(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")

    # Reset config with custom values
    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=4,
    #     chunk_width_in_mm_units=2,
    #     mm_block_unit_ht=2,
    #     mm_M_unit_blocks_per_core=4,
    #     mm_N_blocks_per_slice=2,
    #     ring_size=2,
    #     N_block_idx=0,
    #     M_block_idx=1,
    #     slice_actual_idx=0,
    # ))
    # config.cfg.print_config()

    # params = ReadTilesGranularParams(
    #     worker_id=0,
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     advance_by_tiles=2,
    #     last_mm_core_idx=3,
    #     tile_granularity=5,
    #     direction=0
    # )
    # slice_idxs, global_idxs = read_tiles_granular_from_params_with_direction(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")


    # Reset config with custom values
    # reset_config(GridConfig(
    #     mm_block_unit_wt=4,
    #     mm_blocks_per_N_block=2,
    #     chunk_width_in_mm_units=2,
    #     mm_block_unit_ht=4,
    #     mm_M_unit_blocks_per_core=2,
    #     mm_N_blocks_per_slice=2,
    #     ring_size=2,
    #     N_block_idx=0,
    #     M_block_idx=0,
    #     slice_actual_idx=0,
    # ))
    # config.cfg.print_config()

    # params = ReadTilesGranularParams(
    #     worker_id=1,
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     advance_by_tiles=3,
    #     last_mm_core_idx=3,
    #     tile_granularity=4,
    #     direction=1,
    #     chunk_idx=0
    # )
    # slice_idxs, global_idxs = read_tiles_granular_from_params_with_direction(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")

    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=1,
    #     chunk_width_in_mm_units=1,
    #     mm_block_unit_ht=2,
    #     mm_M_unit_blocks_per_core=1,
    #     mm_N_blocks_per_slice=1,
    #     ring_size=8,
    #     N_block_idx=0,
    #     M_block_idx=0,
    #     slice_actual_idx=0,
    # ))
    # config.cfg.print_config()

    # params = ReadTilesGranularParams(
    #     worker_id=1,
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     advance_by_tiles=2,
    #     last_mm_core_idx=0,
    #     tile_granularity=8,
    #     direction=1,
    #     chunk_idx=0
    # )
    # slice_idxs, global_idxs = read_tiles_granular_from_params_with_direction(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")
    # print("STARTING TESTING CHIP 0_______________")
    # for worker_id in [0, 1]:
    #     print(f"NEXT WORKER_______________{worker_id}______________________")
    #     direction = 0
    #     print(f"DIRECTION_______________{direction}____________________")
    #     for i in [1, 2, 3, 4, 5, 6, 7, 0]:
    #         print(f"worker_id: {worker_id}, direction: {direction}, slice_actual_idx: {i}")
    #         reset_config(GridConfig(
    #             mm_block_unit_wt=2,
    #             mm_blocks_per_N_block=1,
    #             chunk_width_in_mm_units=1,
    #             mm_block_unit_ht=2,
    #             mm_M_unit_blocks_per_core=1,
    #             mm_N_blocks_per_slice=1,
    #             ring_size=8,
    #             N_block_idx=0,
    #             M_block_idx=0,
    #             slice_actual_idx=i,
    #         ))
    #         params = ReadTilesGranularParams(
    #             worker_id=worker_id,
    #             start_tile_row_in_mm_M_block=0,
    #             start_chunk_col_in_tiles=0,
    #             start_mm_core_idx=0,
    #             advance_by_tiles=2,
    #             last_mm_core_idx=0,
    #             tile_granularity=8,
    #             direction=direction,
    #             chunk_idx=0
    #         )
    #         slice_idxs, global_idxs = read_tiles_granular_from_params_with_direction(params)
    #         print(f"global_idxs: {global_idxs}")

    # Reset config with custom values
    # reset_config(GridConfig(
    #     mm_block_unit_wt=2,
    #     mm_blocks_per_N_block=4,
    #     chunk_width_in_mm_units=2,
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
    #     worker_id=0,
    #     start_tile_row_in_mm_M_block=0,
    #     start_chunk_col_in_tiles=0,
    #     start_mm_core_idx=0,
    #     last_mm_core_idx=3,
    #     tile_granularity=4,
    #     direction=0,
    #     num_workers=2
    # )
    # slice_idxs, global_idxs = read_tiles_granular_with_direction_based_on_num_workers_from_params(params)
    # print(f"slice_idxs: {slice_idxs}")
    # print(f"global_idxs: {global_idxs}")

    # Reset config with custom values
    reset_config(GridConfig(
        mm_block_unit_wt=4,
        mm_blocks_per_N_block=2,
        chunk_width_in_mm_units=2,
        mm_block_unit_ht=4,
        mm_M_unit_blocks_per_core=2,
        mm_N_blocks_per_slice=2,
        ring_size=2,
        N_block_idx=0,
        M_block_idx=0,
        slice_actual_idx=0,
    ))
    config.cfg.print_config()

    params = ReadTilesGranularParams(
        worker_id=1,
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        last_mm_core_idx=3,
        tile_granularity=4,
        direction=1,
        chunk_idx=0,
        num_workers=3
    )
    slice_idxs, global_idxs = read_tiles_granular_with_direction_based_on_num_workers_from_params(params)
    print(f"slice_idxs: {slice_idxs}")
    print(f"global_idxs: {global_idxs}")