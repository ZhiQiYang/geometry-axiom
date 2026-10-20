import math, sys
def scene(n):
    A, Z, best = 27, 2500, None
    for m in range(1, 61):
        if m > n - 5: break
        r = max(1, -(-(n - 4 - m) // (m + 1)))
        if r > 60: continue
        w = 916 + 918 * (m - 1) + 14 + 891 + A; h = 363 + 367 * (r - 1) + 14 + 295 + A
        s = abs(math.log(w / h / 1.04)) + 0.01 * (4 + m + (m + 1) * r - n) / n
        if best is None or s < best[0] - 1e-12: best = (s, m, r, w, h)
    _, m, r, w, h = best
    us = [916 + 918 * i for i in range(m)]; vs = [363 + 367 * j for j in range(r)]
    L = ["surface 1 origin 0 0 %d u +x v +y outline 0,0 %d,0 %d,%d 0,%d" % (Z, w, w, h, h),
         "grid 1 on 1 u %s v %s" % (" ".join(map(str, us)), " ".join(map(str, vs)))]
    def t(i, role, place): L.extend(["timber %d 27 33 role %s" % (i, role), "place %d on 1 %s" % (i, place)])
    t(1, "boundary", "at-face e0 between e3 e1 +u +n"); t(2, "boundary", "at-face e2 between e3 e1 -u +n")
    mains = [3 + i for i in range(m)]; wl, wr = 3 + m, 4 + m
    for i, k in enumerate(mains): t(k, "primary", "at-line grid 1 u %d between t1 t2 +v +n" % i)
    t(wl, "primary", "at-face e3 between t1 t2 -v +n"); t(wr, "primary", "at-face e1 between t1 t2 +v +n")
    k = 5 + m
    for bay in range(m + 1):
        left = wl if bay == 0 else mains[bay - 1]; right = wr if bay == m else mains[bay]
        for j in range(r):
            if k > n: break
            t(k, "secondary", "at-line grid 1 v %d between t%d t%d +u +n" % (j, left, right)); k += 1
    return "\n".join(L) + "\n"
if __name__ == "__main__":
    sys.stdout.write(scene(int(sys.argv[1])))
