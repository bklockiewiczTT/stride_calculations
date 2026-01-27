from dataclasses import dataclass


@dataclass
class GridConfig:
    # Primary config values
    mm_block_unit_wt: int = 2
    mm_blocks_per_N_block: int = 4
    chunk_width: int = 3
    mm_block_unit_ht: int = 2
    mm_M_unit_blocks_per_core: int = 4
    mm_N_blocks_per_slice: int = 2
    ring_size: int = 2
    N_block_idx: int = 0 # index of the full N-block within the slice
    M_block_idx: int = 0 # index of the mm M-block within the core
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
        # print("Computing derived values...")
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


# Global config instance
cfg = GridConfig()


def reset_config(new_cfg: GridConfig = None):
    """Reset global config to a new instance or default."""
    global cfg
    cfg = new_cfg if new_cfg is not None else GridConfig()
