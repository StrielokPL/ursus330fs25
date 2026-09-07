"""Run with system liblua (or use `lua tests/regression.lua .`). No third-party Python packages."""
import ctypes, ctypes.util
from pathlib import Path
lib = ctypes.CDLL(ctypes.util.find_library('lua5.4') or ctypes.util.find_library('lua5.3'))
lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
lib.luaL_loadbufferx.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_char_p]
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
lib.lua_close.argtypes=[ctypes.c_void_p]
def run(code,name,compile_only=False):
    state=lib.luaL_newstate();lib.luaL_openlibs(state);data=code.encode()
    rc=lib.luaL_loadbufferx(state,data,len(data),name.encode(),None)
    if rc==0 and not compile_only:rc=lib.lua_pcallk(state,0,-1,0,0,None)
    if rc:
        message=lib.lua_tolstring(state,-1,None).decode();lib.lua_close(state);raise RuntimeError(message)
    lib.lua_close(state)
root=Path(__file__).resolve().parent.parent
for path in root.glob('Scripts/*.lua'):run(path.read_text(),str(path),True)
import os
os.chdir(root)
run((root/'tests/regression.lua').read_text(),'regression')
print('All script syntax checks passed.')
