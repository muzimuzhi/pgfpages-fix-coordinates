from collections import deque
from typing import *
from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.generic import *


def show_info(*objs, pre=None):
    for o in objs:
        if pre is not None:
            print(pre)
        print('TYPE:', type(o))
        print('CONT:', o)
        print()
