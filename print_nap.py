# print_nap.py
#
# prints the specified nap file to stdout

import sys
from crawler2.nap import Nap

def main(napfile):
    nap = Nap(napfile)

    nap_hashcnt = len(nap.dict.keys())
    print(f"{nap_hashcnt} unique links (hashes) found\n")

    for k,v in nap.dict.items():
        print(f"BEGIN HASH {k}")
        print("-------------------------------")
        for k2,v2 in v.items():
            if k2=="words":
                print(f"{k2}\n")
                if v2:
                    for w,c in v2.items():
                        try:
                            print(w,c)
                        except Exception:
                            print("<encoding error>", w.encode("utf-8"), c)
                else:
                    print("<None>")
            elif k2 == "links":
                print(f"{k2}\n")
                if v2:
                    for l in v2:
                        print(l)
                else:
                    print("<None>")
            else:
                print(f"{k2}\t{v2}")
            print("-------------------------------")
        print(f"END HASH {k}")
        print("\n\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python print_nap.py <napfile>")
        sys.exit(1)
    main(sys.argv[1])

