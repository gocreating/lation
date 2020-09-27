import logging
import os
from datetime import datetime

from lation.file_manager import FileManager

# https://shian420.pixnet.net/blog/post/350291572-%5Bpython%5D-logging-%E5%B9%AB%E4%BD%A0%E7%B4%80%E9%8C%84%E4%BB%BB%E4%BD%95%E8%A8%8A%E6%81%AF
def create_logger():
    lation_logger = logging.getLogger()
    lation_logger.setLevel(logging.INFO)
    dir_path = FileManager.prepare_dir(os.path.join(os.getcwd(), 'logs'))

    # file handler
    filename = '{:%Y-%m-%d %H-%M-%S.%f}.log'.format(datetime.now())
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler = logging.FileHandler(os.path.join(dir_path, filename), 'a', 'utf-8')
    file_handler.setFormatter(formatter)
    lation_logger.addHandler(file_handler)

    # console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    lation_logger.addHandler(console_handler)

    return lation_logger
