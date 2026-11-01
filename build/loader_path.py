"""Contorno do Brasil (maior massa contínua dos biomas 1-6 de data/ids.png) como caminho SVG simplificado, para a animação de carregamento."""
import os
from PIL import Image

def brasil_path(root, F=6, eps=0.9, ids=range(1, 7)):
    im = Image.open(os.path.join(root, "data/ids.png"))
    sm = Image.frombytes('L',im.size,bytes(255 if v in ids else 0 for v in im.tobytes())).resize((im.width//F,im.height//F),Image.NEAREST)
    W,H=sm.size; d=sm.load()
    g=lambda x,y: 0<=x<W and 0<=y<H and d[x,y]>0
    # maior componente (flood fill iterativo)
    seen=set(); best=None
    for y in range(H):
      for x in range(W):
        if g(x,y) and (x,y) not in seen:
          st=[(x,y)]; seen.add((x,y)); comp=[]
          while st:
            a,b=st.pop(); comp.append((a,b))
            for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
              n=(a+dx,b+dy)
              if g(*n) and n not in seen: seen.add(n); st.append(n)
          if best is None or len(comp)>len(best): best=comp
    cs=set(best); start=min(best,key=lambda p:(p[1],p[0]))
    # Moore neighbour tracing
    dirs=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
    cur=start; b=4; path=[cur]
    while True:
      for k in range(8):
        i=(b+1+k)%8; n=(cur[0]+dirs[i][0],cur[1]+dirs[i][1])
        if n in cs:
          b=(i+4)%8; cur=n; break
      if cur==start and len(path)>2: break
      path.append(cur)
      if len(path)>200000: break
    def dp(p,e):
      if len(p)<3: return p
      (x1,y1),(x2,y2)=p[0],p[-1]; L=((x2-x1)**2+(y2-y1)**2)**.5 or 1
      dm,im_=0,0
      for i in range(1,len(p)-1):
        dd=abs((y2-y1)*p[i][0]-(x2-x1)*p[i][1]+x2*y1-y2*x1)/L
        if dd>dm: dm,im_=dd,i
      if dm>e: return dp(p[:im_+1],e)[:-1]+dp(p[im_:],e)
      return [p[0],p[-1]]
    h2=len(path)//2; s = dp(path[:h2+1], eps)[:-1] + dp(path[h2:] + [path[0]], eps)[:-1]
    sc=im.width/W
    xs=[p[0] for p in s]; ys=[p[1] for p in s]
    x0,y0=min(xs)-1,min(ys)-1; w=max(xs)-x0+2; h=max(ys)-y0+2
    d = "M" + "L".join(f"{p[0]-x0},{p[1]-y0}" for p in s) + "Z"
    return d, w, h
