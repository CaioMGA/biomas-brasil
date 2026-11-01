import sys, io, zipfile, urllib.request
class H(io.RawIOBase):
    def __init__(s,u):
        s.u=u; s.p=0
        r=urllib.request.Request(u,method="HEAD"); s.n=int(urllib.request.urlopen(r,timeout=60).headers["Content-Length"])
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.p
    def seek(s,o,w=0):
        s.p = o if w==0 else s.p+o if w==1 else s.n+o; return s.p
    def read(s,k=-1):
        if k<0 or s.p+k>s.n: k=s.n-s.p
        if k<=0: return b""
        r=urllib.request.Request(s.u,headers={"Range":f"bytes={s.p}-{s.p+k-1}"})
        d=urllib.request.urlopen(r,timeout=120).read(); s.p+=len(d); return d
    def readinto(s,b):
        d=s.read(len(b)); b[:len(d)]=d; return len(d)
u=sys.argv[1]; z=zipfile.ZipFile(io.BufferedReader(H(u),buffer_size=1<<20))
mode=sys.argv[2]
if mode=="ls":
    for i in z.infolist():
        if any(k in i.filename.lower() for k in sys.argv[3:]) or len(sys.argv)==3: print(i.file_size, i.filename)
else:
    out=sys.argv[3]
    for n in sys.argv[4:]:
        z.extract(n,out); print("ok",n)
