import os

def untar(prefix: str, data):
    def get_filename(remain_data) -> str:
        return remain_data[:100].decode().replace("\x00", "")
    def write_file(filename, remain_data) -> int:
        size = int(data[124:135].decode(), 8)
        file_end = 512 + size
        with open(filename, "wb") as f:
            f.write(remain_data[512:file_end])
        return (file_end // 512 + 1) * 512
    def is_eoa(remain_data):
        if len(remain_data) < 1024:
            return True
        for i in range(1024):
            if remain_data[i] != 0:
                return False
        return True

    def mkdir_filename(filename: str):
        if "/" not in filename:
            return
        path_list = filename.split("/")[:-1]
        for i in range(1, len(path_list) + 1):
            try:
                os.mkdir("/".join(path_list[:i]))
            except:
                pass

    next_block = 0
    while True:
        remain_data = data[next_block:]
        filename = prefix + get_filename(remain_data)
        mkdir_filename(filename)
        next_block += write_file(filename, remain_data)
        if is_eoa(data[next_block:]):
            break
