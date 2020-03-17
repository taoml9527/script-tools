#!/bin/bash

target_dir=$1

cat "/home/gwen/Security/tools/Mobile Apps/apk-regexp.txt" | while read -r r; do
	echo "$r" | awk -F ";;" '{print $1}'
	reg=`echo "$r" | awk -F ";;" '{print $2}'`
	escape_reg=$reg
	escape_reg=$(echo $escape_reg | sed "s/\"/\\\\\"/g")
	echo $escape_reg
	egrep --color -ri "$escape_reg" $target_dir
	echo
	echo
done
