import hashlib

merchant_id = "70840"
amount = "299"
order_str = "Оплатить SPIC 1 мес."
secret1 = "HE{B+3-6FP1v=6o"
target = "7e57a9098f57b3187a37ad93d5133e5c"

def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

candidates = {
    "m:oa:secret1:o": f"{merchant_id}:{amount}:{secret1}:{order_str}",
    "m:oa:secret1":    f"{merchant_id}:{amount}:{secret1}",
    "m:oa:o:secret1": f"{merchant_id}:{amount}:{order_str}:{secret1}",
}

for name, s in candidates.items():
    h = md5(s)
    print(name, "=>", s, "=>", h, "MATCH" if h == target else "")