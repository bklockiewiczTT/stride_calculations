from dataclasses import dataclass
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


@dataclass
class GridConfig:
    # Primary config values
    mm_block_unit_wt: int = 2
    mm_blocks_per_N_block: int = 4
    chunk_width: int = 2
    mm_block_unit_ht: int = 2
    mm_M_unit_blocks_per_core: int = 4
    mm_N_blocks_per_slice: int = 2
    ring_size: int = 2
    N_block_idx: int = 0
    M_block_idx: int = 0
    chunk_idx: int = 0
    slice_actual_idx: int = 0

    # Derived values (computed in __post_init__)
    N_block_wt: int = 0
    slice_Wt: int = 0
    tiles_ht_per_core: int = 0
    chunk_width_in_tiles: int = 0
    chunk_piece_size: int = 0
    global_Wt: int = 0

    def __post_init__(self):
        self.recompute_derived()

    def recompute_derived(self):
        """Recompute derived values from primary config."""
        self.N_block_wt = self.mm_block_unit_wt * self.mm_blocks_per_N_block
        self.slice_Wt = self.N_block_wt * self.mm_N_blocks_per_slice
        self.tiles_ht_per_core = self.mm_block_unit_ht * self.mm_M_unit_blocks_per_core
        self.chunk_width_in_tiles = self.chunk_width * self.mm_block_unit_wt
        self.chunk_piece_size = self.mm_block_unit_ht * self.chunk_width_in_tiles
        self.global_Wt = self.slice_Wt * self.ring_size

    def print_config(self):
        """Print all config values."""
        print(f"tiles_ht_per_core: {self.tiles_ht_per_core}")
        print(f"chunk_piece_size: {self.chunk_piece_size}")
        print(f"chunk_width_in_tiles: {self.chunk_width_in_tiles}")
        print(f"N_block_wt: {self.N_block_wt}")
        print(f"slice_Wt: {self.slice_Wt}")
        print(f"slice_actual_idx: {self.slice_actual_idx}")
        print(f"global_Wt: {self.global_Wt}")
        print(f"N_block_idx: {self.N_block_idx}")
        print(f"M_block_idx: {self.M_block_idx}")
        print(f"chunk_idx: {self.chunk_idx}")


# Global config instance
cfg = GridConfig()


def reset_config(new_cfg: GridConfig = None):
    """Reset global config to a new instance or default."""
    global cfg
    cfg = new_cfg if new_cfg is not None else GridConfig()


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
        tile_granularity=params.tile_granularity
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
    rows_before_this_core = mm_M_block * cfg.tiles_ht_per_core
    rows_before_slice = M_block_idx * cfg.mm_block_unit_ht
    slice_row = rows_before_this_core + rows_before_slice + row_in_mm
    slice_col = N_block_idx * N_block_wt + chunk_idx * cfg.chunk_width_in_tiles + chunk_col
    return slice_row, slice_col

def slice_coordinates_to_slice_tile_index(
    slice_row: int,
    slice_col: int):
    """
    Convert the slice coordinates to the tile index.
    """
    tile_index = slice_row * cfg.slice_Wt + slice_col
    return tile_index

def slice_coordinates_to_global_tile_index(
    slice_row: int,
    slice_col: int):
    """
    Convert the slice coordinates to the global tile index.
    """
    global_col = slice_col + cfg.slice_actual_idx * cfg.slice_Wt
    global_row = slice_row
    return global_row * cfg.global_Wt + global_col

def read_tiles_granular(
    worker_id: int,
    start_row_in_mm: int,
    start_chunk_col: int,
    start_mm_M_block: int,
    advance_by_tiles: int,
    last_mm_M_block: int,
    tile_granularity: int
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

    first_row_in_mm, first_chunk_col, first_mm_M_block = read_next_tile(start_row_in_mm, start_chunk_col, start_mm_M_block, worker_id)
    if first_mm_M_block > last_mm_M_block:
        return
    tiles_to_read = how_many_tiles_to_read_formula(first_row_in_mm, first_chunk_col, first_mm_M_block, advance_by_tiles, last_mm_M_block)
    while tiles_to_read > 0:
        print(f"--------------------------------")
        print(f"tiles_to_read: {tiles_to_read}")
        tiles_to_read_in_this_step = min(tiles_to_read, tile_granularity)
        tiles_to_read -= tiles_to_read_in_this_step
        for i in range(tiles_to_read_in_this_step):
            slice_row, slice_col = coordinates_to_slice_coordinates(first_row_in_mm, first_chunk_col, first_mm_M_block, cfg.N_block_idx, cfg.M_block_idx, cfg.chunk_idx, cfg.N_block_wt)
            # read_tile_coords(i, first_row_in_mm, first_chunk_col, first_mm_M_block)
            # print(f"slice_row: {slice_row}, slice_col: {slice_col}")
            first_row_in_mm, first_chunk_col, first_mm_M_block = read_next_tile(first_row_in_mm, first_chunk_col, first_mm_M_block, advance_by_tiles)
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
    #     chunk_idx=0,
    #     slice_actual_idx=0,
    # ))
    # cfg.print_config()

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
        chunk_width=3,
        mm_block_unit_ht=2,
        mm_M_unit_blocks_per_core=4,
        mm_N_blocks_per_slice=2,
        ring_size=2,
        N_block_idx=0,
        M_block_idx=0,
        chunk_idx=0,
        slice_actual_idx=0,
    ))
    cfg.print_config()

    # params = ReadTilesGranularParams(
    #     worker_id=0,
    #     start_row_in_mm=0,
    #     start_chunk_col=0,
    #     start_mm_M_block=0,
    #     advance_by_tiles=1,
    #     last_mm_M_block=3,
    #     tile_granularity=5
    # )
    # read_tiles_granular_from_params(params)