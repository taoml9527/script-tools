#!/bin/bash

target_dir=$1

cat "/home/gwen/Security/tools/Flash (SWF) application/flash-regexp.txt" | while read -r r; do
	echo "$r" | awk -F ";;" '{print $1" : "$2}'
	reg=`echo "$r" | awk -F ";;" '{print $3}'`
	escape_reg=$reg
	escape_reg=$(echo $escape_reg | sed "s/\"/\\\\\"/g")
	echo $escape_reg
	egrep --color -ri "$escape_reg" $target_dir
	echo
	echo
done
