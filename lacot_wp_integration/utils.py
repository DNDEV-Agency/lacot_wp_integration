def make_batches(input_list, batch_size):
    result = [
        input_list[i : i + batch_size] for i in range(0, len(input_list), batch_size)
    ]
    return result