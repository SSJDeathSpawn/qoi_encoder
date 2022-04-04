from typing import Union
import sys
import numpy as np
from functools import reduce

from chunks import HeaderChunk, IndexChunk, DiffChunk, LumaChunk, EndChunk, RGBAChunk, InvalidChunk, RGBChunk, RunChunk

class QOIFile(object):
    def __init__(self, raw_data: Union[list, tuple, np.ndarray], row_outer=True) -> None:

        self.rows = len(raw_data)
        self.columns = len(raw_data[0])

        if len(raw_data[0][0]) not in (3,4):
            raise ValueError("Unknown colour specification (not RGB or RGBA)")

        raw_data = np.asarray(raw_data)

        data = raw_data.reshape((self.rows*self.columns, len(raw_data[0][0])))

        self.chunks = [HeaderChunk(self.columns, self.rows, len(raw_data[0][0]))]

        self.process_data(data, len(data[0]))

        self.chunks.append(EndChunk())


    def process_data(self, raw_data: Union[list, tuple, np.ndarray], channels: int) -> None:
        sliding_window = [None]*64
        if channels == 4:
            colour_byte = RGBAChunk
        elif channels == 3:
            colour_byte = RGBChunk
        else:
            raise ValueError("Invalid number of channels")

        pointer = 0
        
        def comparable1(pixel1: Union[list, tuple, np.ndarray], pixel2: Union[list, tuple, np.ndarray]) -> bool:
            return all(map(lambda x,y: -2 <= (y-x) <= 1 , pixel1[:3], pixel2[:3])) and pixel1[3] == pixel2[3]
        
        def comparable2(pixel1: Union[list, tuple, np.ndarray], pixel2: Union[list, tuple, np.ndarray]) -> bool:
            return -32 <= pixel2[1] - pixel1[1] <= 31 and all(map(lambda x,y: -8 <= (y-x-(pixel2[1]-pixel1[1])) <= 7, pixel1[:3:2],pixel2[:3:2])) and pixel1[3]== pixel2[3]
        
        def index(pixel: Union[list, tuple, np.ndarray]) -> int:
            return (pixel[0]*3+pixel[1]*5+pixel[2]*7+(pixel[3]*11 if channels==4 else 255*11)) % 64

        while pointer < self.rows*self.columns:
            if pointer > 0:
                if (raw_data[pointer] == raw_data[pointer-1]).all():
                    length = 1
                    while pointer+length < self.rows*self.columns and (raw_data[pointer] == raw_data[pointer+length]).all() and length < 62:
                        length+=1
                    self.chunks.append(RunChunk(length-1))
                    pointer += length-1

                elif (sliding_window[(index(raw_data[pointer]))] == raw_data[pointer]).all():
                    self.chunks.append(IndexChunk(index(raw_data[pointer])))
                
                elif (comparable1(raw_data[pointer-1], raw_data[pointer])):
                    dc = list(map(lambda x,y: y-x+2, raw_data[pointer-1], raw_data[pointer]))
                    self.chunks.append(DiffChunk(*(dc[:3])))
                
                elif (comparable2 (raw_data[pointer-1], raw_data[pointer])):
                    dc = list(map(lambda x,y: y-x, raw_data[pointer-1], raw_data[pointer]))
                    self.chunks.append(LumaChunk(dc[1]+32, dc[0] - dc[1] + 8, dc[2] - dc[1] + 8))
                else:
                    self.chunks.append(colour_byte(raw_data[pointer]))
            else:
                self.chunks.append(colour_byte(raw_data[pointer]))
            sliding_window[index(raw_data[pointer])] = raw_data[pointer]
            pointer += 1

    def __bytes__(self) -> bytes:
        return reduce(lambda x,y: x+bytes(y), self.chunks,b'')