DEFAULT_BATCH_SIZE = 100

def make_batches(input_list, batch_size=DEFAULT_BATCH_SIZE):
    result = [
        input_list[i : i + batch_size] for i in range(0, len(input_list), batch_size)
    ]
    return result
