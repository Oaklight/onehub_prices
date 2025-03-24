import os
import sys


_current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.extend([_current_dir])

from utils import get_channel_id_mapping

if __name__ == "__main__":
    get_channel_id_mapping(save_to_file=True)
