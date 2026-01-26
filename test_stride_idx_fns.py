import config
from config import GridConfig, reset_config
from stride_idx_fns import ReadTilesGranularParams, read_tiles_granular_from_params, read_tiles_granular_from_params_with_direction


def test_basic_configuration():
    """Test read_tiles_granular with configuration from stride_idx_fns.py lines 202-225."""
    # Reset config with custom values (from lines 202-214)
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

    # Create params (from lines 217-225)
    params = ReadTilesGranularParams(
        worker_id=0,
        start_row_in_mm=0,
        start_chunk_col=0,
        start_mm_M_block=0,
        advance_by_tiles=2,
        last_mm_M_block=3,
        tile_granularity=4
    )

    # Execute
    slice_idxs, global_idxs = read_tiles_granular_from_params(params)

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[0, 2, 16, 18], [128, 130, 144, 146], [256, 258, 272, 274], [384, 386, 400, 402]]
    expected_global_idxs = [[0, 2, 32, 34], [256, 258, 288, 290], [512, 514, 544, 546], [768, 770, 800, 802]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_with_direction_backward():
    """Test read_tiles_granular_with_direction from stride_idx_fns.py lines 339-366."""
    # Reset config with custom values (from lines 340-351)
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

    # Create params (from lines 354-363)
    params = ReadTilesGranularParams(
        worker_id=1,
        start_row_in_mm=0,
        start_chunk_col=0,
        start_mm_M_block=0,
        advance_by_tiles=2,
        last_mm_M_block=3,
        tile_granularity=4,
        direction=1
    )

    # Execute
    slice_idxs, global_idxs = read_tiles_granular_from_params_with_direction(params)

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[3, 19, 131, 147], [259, 275, 387, 403]]
    expected_global_idxs = [[3, 35, 259, 291], [515, 547, 771, 803]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_slice_actual_idx_1():
    """Test read_tiles_granular with slice_actual_idx=1 and advance_by_tiles=3."""
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
        slice_actual_idx=1,
    ))

    params = ReadTilesGranularParams(
        worker_id=0,
        start_row_in_mm=0,
        start_chunk_col=0,
        start_mm_M_block=0,
        advance_by_tiles=3,
        last_mm_M_block=2,
        tile_granularity=5,
        chunk_idx=0
    )

    # Execute
    slice_idxs, global_idxs = read_tiles_granular_from_params(params)

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[0, 3, 18, 129, 144], [147, 258, 273]]
    expected_global_idxs = [[16, 19, 50, 273, 304], [307, 530, 561]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_chunk_width_3_chunk_idx_1():
    """Test read_tiles_granular with chunk_width=3 and chunk_idx=1."""
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
        slice_actual_idx=0,
    ))

    params = ReadTilesGranularParams(
        worker_id=1,
        start_row_in_mm=0,
        start_chunk_col=0,
        start_mm_M_block=0,
        advance_by_tiles=2,
        last_mm_M_block=3,
        tile_granularity=5,
        chunk_idx=1
    )

    # Execute
    slice_idxs, global_idxs = read_tiles_granular_from_params(params)

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[7, 23, 135, 151, 263], [279, 391, 407]]
    expected_global_idxs = [[7, 39, 263, 295, 519], [551, 775, 807]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"
