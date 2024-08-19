import os
import sys

os_type = os.name

path_separator = '\\' if os_type == 'nt' else '/'


def init():
    global path
    path = path_separator


init()


def mkdir_if_necessary(create_dir):
    try:
        # 在Windows上，如果路径是绝对的，则需要确保它以盘符开头
        if os_type == 'nt' and os.path.isabs(create_dir):
            if len(create_dir) < 2 or create_dir[1] != ':':
                raise ValueError("Invalid absolute path for Windows")
        os.makedirs(create_dir, exist_ok=True)  # Python 3.2+
        return None
    except OSError as e:
        return e


def get_current_path():
    # 获取当前执行文件的目录
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def is_file_exist(file_path):
    if not file_path:
        return False
    return os.path.exists(file_path)


def read_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
        return file_content
    except IOError as e:
        print(f"An error occurred while reading the file: {e}")
        return None

