#!/bin/bash
#
# scripts/depthcnt.sh
#
# compiles depth counts up to max_count
# for nurls in frontier.nap
#
# usage: scripts/count.sh <naplog> <max_count>

if [ $# -lt 2 ]; then
	echo "error: too few args specified"
	exit 1
fi

pipe="$(cat "$1" | grep -P "depth\t")"

# up to max_count
# print depth counts
for ((i = 0; i<=$2; i++)); do
	printf "i=$i:\n"

	# grep patterns
	ap="absdepth\t$i\$"
	rp="reldepth\t$i\$"
	mp="monodepth\t$i\$"
	dp="dupdepth\t$i\$"

	# grep output
	a=$(echo "$pipe" | grep -Pc $ap)
	r=$(echo "$pipe" | grep -Pc $rp)
	m=$(echo "$pipe" | grep -Pc $mp)
	d=$(echo "$pipe" | grep -Pc $dp)

	# print results
	printf "absdepth: $a\n"
	printf "reldepth: $r\n"
	printf "monodepth: $m\n"
	printf "dupdepth: $d\n\n"
done

