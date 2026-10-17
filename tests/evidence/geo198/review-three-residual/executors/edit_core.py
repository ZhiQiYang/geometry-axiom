import pathlib
p=pathlib.Path('/workspace/geometry-axiom/current_geometry.c');data=p.read_bytes()
assert data.count(b'\n')==data.count(b'\r\n') and b'\0' not in data
start=data.index(b'static bool proj_split_loop(');end=data.index(b'/* \xe6\x8b\x86\xe5\x88\x86\xe5\xbe\x8c\xe5\xad\x94',start)
block=data[start:end]
old=b'    size_t pc = 0, n = loop->count;\r\n';assert block.count(old)==1
block=block.replace(old,old+b'    size_t covered_runs = 0;\r\n')
old=b'        if (!in_run) {\r\n            in_run = true;\r\n';assert block.count(old)==1
block=block.replace(old,b'        if (!in_run) {\r\n            /* A third covered arc separates a third residue. Cycling back\r\n             * to pieces[0] would reconnect it through the removed rectangle. */\r\n            if (++covered_runs > 2) return false;\r\n            in_run = true;\r\n')
p.write_bytes(data[:start]+block+data[end:])
assert p.read_bytes().count(b'\n')==p.read_bytes().count(b'\r\n')
