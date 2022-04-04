from exceptions import InvalidChunk 
import sys
from typing import Union

class Chunk(object):

    def __init_subclass__(cls) -> None:
        if not (getattr(cls, 'marker')!=None and getattr(cls, 'chunk_size')!=None):
            raise InvalidChunk() 

    def __bytes__(self) -> bytes:
        if getattr(self, 'data')==None:
            raise ValueError(f'No data in chunk type {self.__class__}')
        clazz = self.__class__
        if clazz.marker > 4:
            res_raw = clazz.marker * ((2**8)**(clazz.chunk_size//8-1))  + self.data
        else:
            res_raw = clazz.marker * (2**6)
            res_raw += self.data
        if type(res_raw)!= int:
            res_raw = res_raw.item()
        try:
            return int.to_bytes(res_raw, clazz.chunk_size//8, 'big')
        except OverflowError as e:
            print(f'Overflow Error caused by {self.__class__} having data {self.data}')
            exit(-1)


class HeaderChunk(object):

    def __init__(self, width: int, height: int, channels: int) -> None:
        self.width = width
        self.height = height
        self.channels = channels

    def __bytes__(self) -> bytes:
        return bytes('qoif', 'ascii') + self.width.to_bytes(length=4, byteorder='big') + self.height.to_bytes(length=4, byteorder='big') +int.to_bytes(self.channels,1,'big')+ int.to_bytes(1, length=1, byteorder='big')

class RGBChunk(Chunk):
    marker=254
    chunk_size=8*4

    def __init__(self, r: int, g: int, b: int) -> None:
        self.data = r*256*256 + g*256 + b
    
    def __init__(self, data:Union[tuple, list]) -> None:
        self.data = 0
        for i in data:
            self.data = self.data*256+i

class RGBAChunk(Chunk):
    marker=255
    chunk_size=8*5

    def __init__(self, r: int, g: int, b: int, a: int) -> None:
        self.data = r*(256**3) + g*(256**2) + b*256 + a

    def __init__(self, data:Union[tuple, list]) -> None:
        self.data = 0
        for i in data:
            self.data = self.data*256+i
    
class IndexChunk(Chunk):
    marker=0
    chunk_size=8

    def __init__(self, index: int) -> None:
        if not 0 <= index <= 63:
            raise ValueError("Invalid index")
        self.data = index

class DiffChunk(Chunk):
    marker = 1
    chunk_size=8

    def __init__(self, dr: int, dg: int, db: int):
        self.data = dr*(4**2)+dg*(4)+db

class LumaChunk(object):
    marker=2
    chunk_size=16

    def __init__(self, diff_green: int, dr_dg: int, db_dg: int) -> None:
        self.data = LumaChunk.marker*(2**14) + diff_green*(2**8) + dr_dg*(2**4) + db_dg
    
    def __bytes__(self) -> bytes:
        if type(self.data) != int:
            self.data = self.data.item()
        return int.to_bytes(self.data, self.chunk_size//8, 'big')

class RunChunk(Chunk):
    marker= 3
    chunk_size=8

    def __init__(self, run_length: int) -> None:
        if not 0 <= run_length <= 61:
            raise ValueError(f'{run_length} is not an appropriate run length') 
        self.data = run_length

class EndChunk(object):
    def __bytes__(self) -> bytes:
        return int.to_bytes(1, 1, 'big')