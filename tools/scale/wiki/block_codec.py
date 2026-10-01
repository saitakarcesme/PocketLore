"""Bounded standard zlib/Zstandard frames; no dictionaries, workers or network."""
import ctypes,zlib
_zstd=None
def zstd():
 global _zstd
 if _zstd is None:
  lib=ctypes.CDLL('libzstd.so.1');size=ctypes.c_size_t;ptr=ctypes.c_void_p
  for name,args,result in [('ZSTD_compressBound',[size],size),('ZSTD_compress',[ptr,size,ptr,size,ctypes.c_int],size),('ZSTD_decompress',[ptr,size,ptr,size],size),('ZSTD_findFrameCompressedSize',[ptr,size],size),('ZSTD_isError',[size],ctypes.c_uint),('ZSTD_getErrorName',[size],ctypes.c_char_p),('ZSTD_versionString',[],ctypes.c_char_p)]:
   fn=getattr(lib,name);fn.argtypes=args;fn.restype=result
  _zstd=lib
 return _zstd
def checked(value):
 lib=zstd()
 if lib.ZSTD_isError(value):raise ValueError(lib.ZSTD_getErrorName(value).decode())
 return value
def compress(raw,level=6,codec='zlib'):
 if not 0<len(raw)<=128*1024**2:raise ValueError('Raw block bound')
 if codec=='zlib':return zlib.compress(raw,level)
 if codec!='zstd':raise ValueError('Unknown block codec')
 raw=bytes(raw);lib=zstd();capacity=checked(lib.ZSTD_compressBound(len(raw)));target=ctypes.create_string_buffer(capacity)
 n=checked(lib.ZSTD_compress(target,capacity,raw,len(raw),level));return target.raw[:n]
def decompress(packed,raw_length,codec='zlib'):
 if not 0<len(packed)<=64*1024**2 or not 0<raw_length<=128*1024**2:raise ValueError('Block bound')
 if codec=='zlib':
  dec=zlib.decompressobj();raw=dec.decompress(packed,raw_length+1)
  if not dec.eof or dec.unused_data or len(raw)!=raw_length:raise ValueError('Zlib frame length or trailing data')
  return raw
 if codec!='zstd':raise ValueError('Unknown block codec')
 lib=zstd()
 if checked(lib.ZSTD_findFrameCompressedSize(packed,len(packed)))!=len(packed):raise ValueError('Trailing Zstandard frame data')
 target=ctypes.create_string_buffer(raw_length);n=checked(lib.ZSTD_decompress(target,raw_length,packed,len(packed)))
 if n!=raw_length:raise ValueError('Zstandard inflated length')
 return target.raw
