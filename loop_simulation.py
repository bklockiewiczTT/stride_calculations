from stride_idx_fns import read_tiles_granular_with_direction_based_on_num_workers


def get_iteration_history(
    batch_size: int,
    M_blocks_per_core: int,
    chunks_per_mm_N_block: int,
    my_chip_id: int,
    direction: int,
    ring_size: int,
    mm_N_blocks_per_slice: int,
    worker_id: int,
    last_mm_core_idx: int,
    tile_granularity: int,
    num_workers: int,
    mm_block_unit_ht: int,
    chunk_width: int,
    N_block_wt: int,
    tiles_ht_per_core: int,
    slice_Wt: int,
):
    """
    Computes iteration history by iterating through batches, M blocks, chunks,
    ring iterations, and chunk pieces, calling read_tiles_granular_with_direction_based_on_num_workers
    for each combination.
    """
    chunk_width_in_tiles = chunk_width * mm_block_unit_ht
    global_Wt = ring_size * slice_Wt
    effective_worker_id = worker_id + direction * num_workers

    iteration_history = []

    for b in range(batch_size):
        print(f"================================================")
        print(f"batch: {b} started")
        for m_block_iter in range(M_blocks_per_core):
            print(f"--------------------------------")
            print(f"m_block_iter: {m_block_iter} started")
            for chunk_idx in range(chunks_per_mm_N_block):
                print(f"chunk_idx: {chunk_idx} started")
                slice_idx = my_chip_id - 1 if direction == 1 else my_chip_id + 1
                for i in range(ring_size):
                    print(f"************************************************")
                    print(f"ring iteration: {i} started")
                    if direction == 1:
                        actual_slice_idx = slice_idx + ring_size if slice_idx < 0 else slice_idx
                    else:
                        actual_slice_idx = slice_idx - ring_size if slice_idx >= ring_size else slice_idx
                    
                    print(f"actual_slice_idx: {actual_slice_idx}, m_block_iter: {m_block_iter}, chunk_idx: {chunk_idx}")
                    first_tile_row_in_mm_M_block = 0
                    first_chunk_col_in_tiles = 0
                    first_mm_core_idx = 0
                    for chunk_piece_idx in range(mm_N_blocks_per_slice):
                        print(f"chunk_piece_idx: {chunk_piece_idx} started")
                        iteration_id = (b, m_block_iter, chunk_idx, chunk_piece_idx)
                        slice_idxs, global_idxs = read_tiles_granular_with_direction_based_on_num_workers(
                            worker_id=effective_worker_id,
                            start_tile_row_in_mm_M_block=first_tile_row_in_mm_M_block,
                            start_chunk_col_in_tiles=first_chunk_col_in_tiles,
                            start_mm_core_idx=first_mm_core_idx,
                            last_mm_core_idx=last_mm_core_idx,
                            tile_granularity=tile_granularity,
                            chunk_idx=chunk_idx,
                            direction=direction,
                            num_workers=num_workers,
                            mm_block_unit_ht=mm_block_unit_ht,
                            chunk_width_in_tiles=chunk_width_in_tiles,
                            N_block_wt=N_block_wt,
                            N_block_idx=chunk_piece_idx,
                            M_block_idx=m_block_iter,
                            tiles_ht_per_core=tiles_ht_per_core,
                            slice_Wt=slice_Wt,
                            slice_actual_idx=actual_slice_idx,
                            global_Wt=global_Wt,
                        )
                        iteration_history.append((iteration_id, slice_idxs, global_idxs))
                        print(f"chunk_piece_idx: {chunk_piece_idx} done")
                    if direction == 1:
                        slice_idx = slice_idx + 1
                    else:
                        slice_idx = slice_idx - 1
                    print(f"ring iteration: {i} done")
                print(f"chunk_idx: {chunk_idx} done")
            print(f"m_block_iter: {m_block_iter} done")
        print(f"batch: {b} done")

    return iteration_history


if __name__ == "__main__":
    # Input parameters
    batch_size = 1
    M_blocks_per_core = 4
    chunks_per_mm_N_block = 2
    my_chip_id = 0
    direction = 0
    ring_size = 2
    mm_N_blocks_per_slice = 2
    worker_id = 0
    last_mm_core_idx = 3
    tile_granularity = 4
    num_workers = 2
    mm_block_unit_ht = 2
    chunk_width = 2
    N_block_wt = 8
    tiles_ht_per_core = 8
    slice_Wt = 16

    # Derived values for printing
    chunk_width_in_tiles = chunk_width * mm_block_unit_ht
    global_Wt = ring_size * slice_Wt
    effective_worker_id = worker_id + direction * num_workers
    effective_advance_by_tiles = 2 * num_workers

    print(f"batch_size: {batch_size}")
    print(f"M_blocks_per_core: {M_blocks_per_core}")
    print(f"chunks_per_mm_N_block: {chunks_per_mm_N_block}")
    print(f"my_chip_id: {my_chip_id}")
    print(f"direction: {direction}")
    print(f"ring_size: {ring_size}")
    print(f"mm_N_blocks_per_slice: {mm_N_blocks_per_slice}")
    print(f"worker_id: {worker_id}")
    print(f"last_mm_core_idx: {last_mm_core_idx}")
    print(f"tile_granularity: {tile_granularity}")
    print(f"num_workers: {num_workers}")
    print(f"effective_worker_id: {effective_worker_id}")
    print(f"effective_advance_by_tiles: {effective_advance_by_tiles}")

    # Get iteration history using the function
    iteration_history = get_iteration_history(
        batch_size=batch_size,
        M_blocks_per_core=M_blocks_per_core,
        chunks_per_mm_N_block=chunks_per_mm_N_block,
        my_chip_id=my_chip_id,
        direction=direction,
        ring_size=ring_size,
        mm_N_blocks_per_slice=mm_N_blocks_per_slice,
        worker_id=worker_id,
        last_mm_core_idx=last_mm_core_idx,
        tile_granularity=tile_granularity,
        num_workers=num_workers,
        mm_block_unit_ht=mm_block_unit_ht,
        chunk_width=chunk_width,
        N_block_wt=N_block_wt,
        tiles_ht_per_core=tiles_ht_per_core,
        slice_Wt=slice_Wt,
    )

    print(f"iteration_history: {iteration_history}")