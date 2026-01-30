import config
from config import GridConfig, reset_config
from stride_idx_fns import (
    ReadTilesGranularParams,
    read_tiles_granular_from_params,
    read_tiles_granular_from_params_with_direction,
    read_tiles_granular_with_direction_based_on_num_workers_from_params,
    read_tiles_granular_with_direction_based_on_num_workers,
)
from loop_simulation import get_iteration_history


def test_basic_configuration():
    """Test read_tiles_granular with configuration from stride_idx_fns.py lines 202-225."""
    # Reset config with custom values (from lines 202-214)
    reset_config(GridConfig(
        mm_block_unit_wt=2,
        mm_blocks_per_N_block=4,
        chunk_width_in_mm_units=2,
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
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        advance_by_tiles=2,
        last_mm_core_idx=3,
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
        chunk_width_in_mm_units=2,
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
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        advance_by_tiles=2,
        last_mm_core_idx=3,
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
        chunk_width_in_mm_units=2,
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
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        advance_by_tiles=3,
        last_mm_core_idx=2,
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
    """Test read_tiles_granular with chunk_width_in_mm_units=3 and chunk_idx=1."""
    reset_config(GridConfig(
        mm_block_unit_wt=2,
        mm_blocks_per_N_block=4,
        chunk_width_in_mm_units=3,
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
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        advance_by_tiles=2,
        last_mm_core_idx=3,
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


def test_m_block_idx_1():
    """Test read_tiles_granular with M_block_idx=1 and chunk_width_in_mm_units=3."""
    reset_config(GridConfig(
        mm_block_unit_wt=2,
        mm_blocks_per_N_block=4,
        chunk_width_in_mm_units=3,
        mm_block_unit_ht=2,
        mm_M_unit_blocks_per_core=4,
        mm_N_blocks_per_slice=2,
        ring_size=2,
        N_block_idx=0,
        M_block_idx=1,
        slice_actual_idx=0,
    ))

    params = ReadTilesGranularParams(
        worker_id=0,
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        advance_by_tiles=3,
        last_mm_core_idx=3,
        tile_granularity=4,
        chunk_idx=0
    )

    # Execute
    slice_idxs, global_idxs = read_tiles_granular_from_params(params)

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[32, 35, 48, 51], [160, 163, 176, 179], [288, 291, 304, 307], [416, 419, 432, 435]]
    expected_global_idxs = [[64, 67, 96, 99], [320, 323, 352, 355], [576, 579, 608, 611], [832, 835, 864, 867]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_n_block_idx_1_m_block_idx_2():
    """Test read_tiles_granular with N_block_idx=1 and M_block_idx=2."""
    reset_config(GridConfig(
        mm_block_unit_wt=2,
        mm_blocks_per_N_block=4,
        chunk_width_in_mm_units=2,
        mm_block_unit_ht=2,
        mm_M_unit_blocks_per_core=4,
        mm_N_blocks_per_slice=2,
        ring_size=2,
        N_block_idx=1,
        M_block_idx=2,
        slice_actual_idx=0,
    ))

    params = ReadTilesGranularParams(
        worker_id=0,
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        advance_by_tiles=3,
        last_mm_core_idx=3,
        tile_granularity=5,
        chunk_idx=1
    )

    # Execute
    slice_idxs, global_idxs = read_tiles_granular_from_params(params)

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[76, 79, 94, 205, 220], [223, 334, 349, 460, 463], [478]]
    expected_global_idxs = [[140, 143, 174, 397, 428], [431, 654, 685, 908, 911], [942]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_with_direction_forward():
    """Test read_tiles_granular_with_direction with direction=0 (forward) and M_block_idx=1."""
    reset_config(GridConfig(
        mm_block_unit_wt=2,
        mm_blocks_per_N_block=4,
        chunk_width_in_mm_units=2,
        mm_block_unit_ht=2,
        mm_M_unit_blocks_per_core=4,
        mm_N_blocks_per_slice=2,
        ring_size=2,
        N_block_idx=0,
        M_block_idx=1,
        slice_actual_idx=0,
    ))

    params = ReadTilesGranularParams(
        worker_id=0,
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        advance_by_tiles=2,
        last_mm_core_idx=3,
        tile_granularity=5,
        direction=0
    )

    # Execute
    slice_idxs, global_idxs = read_tiles_granular_from_params_with_direction(params)

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[32, 48, 160, 176, 288], [304, 416, 432]]
    expected_global_idxs = [[64, 96, 320, 352, 576], [608, 832, 864]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_different_block_dimensions():
    """Test with different mm_block_unit_wt=4 and mm_block_unit_ht=4."""
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

    params = ReadTilesGranularParams(
        worker_id=1,
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        advance_by_tiles=3,
        last_mm_core_idx=3,
        tile_granularity=4,
        direction=1,
        chunk_idx=0
    )

    # Execute
    slice_idxs, global_idxs = read_tiles_granular_from_params_with_direction(params)

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[4, 18, 32, 38], [52, 130, 144, 150], [164, 178, 256, 262], [276, 290, 304, 310], [388, 402, 416, 422], [436]]
    expected_global_idxs = [[4, 34, 64, 70], [100, 258, 288, 294], [324, 354, 512, 518], [548, 578, 608, 614], [772, 802, 832, 838], [868]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_direction_based_on_num_workers():
    """Test read_tiles_granular_with_direction_based_on_num_workers with num_workers=2."""
    # Config values - no global config needed
    mm_block_unit_wt = 2
    mm_blocks_per_N_block = 4
    chunk_width_in_mm_units = 2
    mm_block_unit_ht = 2
    mm_M_unit_blocks_per_core = 4
    mm_N_blocks_per_slice = 2
    ring_size = 2
    N_block_idx = 0
    M_block_idx = 0
    slice_actual_idx = 0

    # Derived values
    N_block_wt = mm_block_unit_wt * mm_blocks_per_N_block  # 8
    slice_Wt = N_block_wt * mm_N_blocks_per_slice  # 16
    tiles_ht_per_core = mm_block_unit_ht * mm_M_unit_blocks_per_core  # 8
    chunk_width_in_tiles = chunk_width_in_mm_units * mm_block_unit_wt  # 4
    global_Wt = slice_Wt * ring_size  # 32

    # Execute using explicit-parameter version
    slice_idxs, global_idxs = read_tiles_granular_with_direction_based_on_num_workers(
        worker_id=0,
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        last_mm_core_idx=3,
        tile_granularity=4,
        chunk_idx=0,
        direction=0,
        num_workers=2,
        mm_block_unit_ht=mm_block_unit_ht,
        chunk_width_in_tiles=chunk_width_in_tiles,
        N_block_wt=N_block_wt,
        N_block_idx=N_block_idx,
        M_block_idx=M_block_idx,
        tiles_ht_per_core=tiles_ht_per_core,
        slice_Wt=slice_Wt,
        slice_actual_idx=slice_actual_idx,
        global_Wt=global_Wt,
    )

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[0, 16, 128, 144], [256, 272, 384, 400]]
    expected_global_idxs = [[0, 32, 256, 288], [512, 544, 768, 800]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_direction_based_on_num_workers_3():
    """Test read_tiles_granular_with_direction_based_on_num_workers with num_workers=3 and different block dimensions."""
    # Config values - no global config needed
    mm_block_unit_wt = 4
    mm_blocks_per_N_block = 2
    chunk_width_in_mm_units = 2
    mm_block_unit_ht = 4
    mm_M_unit_blocks_per_core = 2
    mm_N_blocks_per_slice = 2
    ring_size = 2
    N_block_idx = 0
    M_block_idx = 0
    slice_actual_idx = 0

    # Derived values
    N_block_wt = mm_block_unit_wt * mm_blocks_per_N_block  # 8
    slice_Wt = N_block_wt * mm_N_blocks_per_slice  # 16
    tiles_ht_per_core = mm_block_unit_ht * mm_M_unit_blocks_per_core  # 8
    chunk_width_in_tiles = chunk_width_in_mm_units * mm_block_unit_wt  # 8
    global_Wt = slice_Wt * ring_size  # 32

    # Execute using explicit-parameter version
    slice_idxs, global_idxs = read_tiles_granular_with_direction_based_on_num_workers(
        worker_id=1,
        start_tile_row_in_mm_M_block=0,
        start_chunk_col_in_tiles=0,
        start_mm_core_idx=0,
        last_mm_core_idx=3,
        tile_granularity=4,
        chunk_idx=0,
        direction=1,
        num_workers=3,
        mm_block_unit_ht=mm_block_unit_ht,
        chunk_width_in_tiles=chunk_width_in_tiles,
        N_block_wt=N_block_wt,
        N_block_idx=N_block_idx,
        M_block_idx=M_block_idx,
        tiles_ht_per_core=tiles_ht_per_core,
        slice_Wt=slice_Wt,
        slice_actual_idx=slice_actual_idx,
        global_Wt=global_Wt,
    )

    # Reference values (list of lists, one per outer while iteration)
    expected_slice_idxs = [[4, 18, 32, 38], [52, 130, 144, 150], [164, 178, 256, 262], [276, 290, 304, 310], [388, 402, 416, 422], [436]]
    expected_global_idxs = [[4, 34, 64, 70], [100, 258, 288, 294], [324, 354, 512, 518], [548, 578, 608, 614], [772, 802, 832, 838], [868]]

    # Assert
    assert slice_idxs == expected_slice_idxs, "slice_idxs mismatch"
    assert global_idxs == expected_global_idxs, "global_idxs mismatch"


def test_get_iteration_history():
    """Test get_iteration_history produces correct iteration history for loop simulation."""
    iteration_history = get_iteration_history(
        batch_size=1,
        M_blocks_per_core=4,
        chunks_per_mm_N_block=2,
        my_chip_id=0,
        direction=0,
        ring_size=2,
        mm_N_blocks_per_slice=2,
        worker_id=0,
        last_mm_core_idx=3,
        tile_granularity=4,
        num_workers=2,
        mm_block_unit_ht=2,
        chunk_width=2,
        N_block_wt=8,
        tiles_ht_per_core=8,
        slice_Wt=16,
    )

    expected_iteration_history = [
        ((0, 0, 0, 0), [[0, 16, 128, 144], [256, 272, 384, 400]], [[16, 48, 272, 304], [528, 560, 784, 816]]),
        ((0, 0, 0, 1), [[8, 24, 136, 152], [264, 280, 392, 408]], [[24, 56, 280, 312], [536, 568, 792, 824]]),
        ((0, 0, 0, 0), [[0, 16, 128, 144], [256, 272, 384, 400]], [[0, 32, 256, 288], [512, 544, 768, 800]]),
        ((0, 0, 0, 1), [[8, 24, 136, 152], [264, 280, 392, 408]], [[8, 40, 264, 296], [520, 552, 776, 808]]),
        ((0, 0, 1, 0), [[4, 20, 132, 148], [260, 276, 388, 404]], [[20, 52, 276, 308], [532, 564, 788, 820]]),
        ((0, 0, 1, 1), [[12, 28, 140, 156], [268, 284, 396, 412]], [[28, 60, 284, 316], [540, 572, 796, 828]]),
        ((0, 0, 1, 0), [[4, 20, 132, 148], [260, 276, 388, 404]], [[4, 36, 260, 292], [516, 548, 772, 804]]),
        ((0, 0, 1, 1), [[12, 28, 140, 156], [268, 284, 396, 412]], [[12, 44, 268, 300], [524, 556, 780, 812]]),
        ((0, 1, 0, 0), [[32, 48, 160, 176], [288, 304, 416, 432]], [[80, 112, 336, 368], [592, 624, 848, 880]]),
        ((0, 1, 0, 1), [[40, 56, 168, 184], [296, 312, 424, 440]], [[88, 120, 344, 376], [600, 632, 856, 888]]),
        ((0, 1, 0, 0), [[32, 48, 160, 176], [288, 304, 416, 432]], [[64, 96, 320, 352], [576, 608, 832, 864]]),
        ((0, 1, 0, 1), [[40, 56, 168, 184], [296, 312, 424, 440]], [[72, 104, 328, 360], [584, 616, 840, 872]]),
        ((0, 1, 1, 0), [[36, 52, 164, 180], [292, 308, 420, 436]], [[84, 116, 340, 372], [596, 628, 852, 884]]),
        ((0, 1, 1, 1), [[44, 60, 172, 188], [300, 316, 428, 444]], [[92, 124, 348, 380], [604, 636, 860, 892]]),
        ((0, 1, 1, 0), [[36, 52, 164, 180], [292, 308, 420, 436]], [[68, 100, 324, 356], [580, 612, 836, 868]]),
        ((0, 1, 1, 1), [[44, 60, 172, 188], [300, 316, 428, 444]], [[76, 108, 332, 364], [588, 620, 844, 876]]),
        ((0, 2, 0, 0), [[64, 80, 192, 208], [320, 336, 448, 464]], [[144, 176, 400, 432], [656, 688, 912, 944]]),
        ((0, 2, 0, 1), [[72, 88, 200, 216], [328, 344, 456, 472]], [[152, 184, 408, 440], [664, 696, 920, 952]]),
        ((0, 2, 0, 0), [[64, 80, 192, 208], [320, 336, 448, 464]], [[128, 160, 384, 416], [640, 672, 896, 928]]),
        ((0, 2, 0, 1), [[72, 88, 200, 216], [328, 344, 456, 472]], [[136, 168, 392, 424], [648, 680, 904, 936]]),
        ((0, 2, 1, 0), [[68, 84, 196, 212], [324, 340, 452, 468]], [[148, 180, 404, 436], [660, 692, 916, 948]]),
        ((0, 2, 1, 1), [[76, 92, 204, 220], [332, 348, 460, 476]], [[156, 188, 412, 444], [668, 700, 924, 956]]),
        ((0, 2, 1, 0), [[68, 84, 196, 212], [324, 340, 452, 468]], [[132, 164, 388, 420], [644, 676, 900, 932]]),
        ((0, 2, 1, 1), [[76, 92, 204, 220], [332, 348, 460, 476]], [[140, 172, 396, 428], [652, 684, 908, 940]]),
        ((0, 3, 0, 0), [[96, 112, 224, 240], [352, 368, 480, 496]], [[208, 240, 464, 496], [720, 752, 976, 1008]]),
        ((0, 3, 0, 1), [[104, 120, 232, 248], [360, 376, 488, 504]], [[216, 248, 472, 504], [728, 760, 984, 1016]]),
        ((0, 3, 0, 0), [[96, 112, 224, 240], [352, 368, 480, 496]], [[192, 224, 448, 480], [704, 736, 960, 992]]),
        ((0, 3, 0, 1), [[104, 120, 232, 248], [360, 376, 488, 504]], [[200, 232, 456, 488], [712, 744, 968, 1000]]),
        ((0, 3, 1, 0), [[100, 116, 228, 244], [356, 372, 484, 500]], [[212, 244, 468, 500], [724, 756, 980, 1012]]),
        ((0, 3, 1, 1), [[108, 124, 236, 252], [364, 380, 492, 508]], [[220, 252, 476, 508], [732, 764, 988, 1020]]),
        ((0, 3, 1, 0), [[100, 116, 228, 244], [356, 372, 484, 500]], [[196, 228, 452, 484], [708, 740, 964, 996]]),
        ((0, 3, 1, 1), [[108, 124, 236, 252], [364, 380, 492, 508]], [[204, 236, 460, 492], [716, 748, 972, 1004]]),
    ]

    assert iteration_history == expected_iteration_history, "iteration_history mismatch"


def test_get_iteration_history_ring_size_8():
    """Test get_iteration_history with ring_size=8, small blocks, and single worker read per chunk."""
    iteration_history = get_iteration_history(
        batch_size=1,
        M_blocks_per_core=2,
        chunks_per_mm_N_block=1,
        my_chip_id=0,
        direction=0,
        ring_size=8,
        mm_N_blocks_per_slice=1,
        worker_id=0,
        last_mm_core_idx=0,
        tile_granularity=8,
        num_workers=2,
        mm_block_unit_ht=2,
        chunk_width=1,
        N_block_wt=2,
        tiles_ht_per_core=4,
        slice_Wt=2,
    )

    expected_iteration_history = [
        ((0, 0, 0, 0), [[0]], [[2]]),
        ((0, 0, 0, 0), [[0]], [[4]]),
        ((0, 0, 0, 0), [[0]], [[6]]),
        ((0, 0, 0, 0), [[0]], [[8]]),
        ((0, 0, 0, 0), [[0]], [[10]]),
        ((0, 0, 0, 0), [[0]], [[12]]),
        ((0, 0, 0, 0), [[0]], [[14]]),
        ((0, 0, 0, 0), [[0]], [[0]]),
        ((0, 1, 0, 0), [[4]], [[34]]),
        ((0, 1, 0, 0), [[4]], [[36]]),
        ((0, 1, 0, 0), [[4]], [[38]]),
        ((0, 1, 0, 0), [[4]], [[40]]),
        ((0, 1, 0, 0), [[4]], [[42]]),
        ((0, 1, 0, 0), [[4]], [[44]]),
        ((0, 1, 0, 0), [[4]], [[46]]),
        ((0, 1, 0, 0), [[4]], [[32]]),
    ]

    assert iteration_history == expected_iteration_history, "iteration_history mismatch"
