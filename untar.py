import os

def untar(prefix, data):
    def get_filename(remain_data) -> str:
        return remain_data[:100].decode().replace("\x00", "")
    def write_file(filename, remain_data) -> int:
        size = int(data[124:136].decode())
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
        d = "/".join(filename.split("/")[:-1])
        try:
            os.mkdir(d)
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
