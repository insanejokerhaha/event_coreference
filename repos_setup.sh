#!/bin/bash
if [ ! -d "./repos" ]; then
	mkdir repos
fi
if [ ! -d "./repos/mappings" ]; then
	mkdir repos/mappings
fi
if [ ! -d "./repos/semafor_srl" ]; then
	mkdir repos/semafor_srl
fi
if [ ! -d "./repos/sesame_srl" ]; then
	mkdir repos/sesame_srl
fi
if [ ! -d "./repos/semafor_annotations" ]; then
	mkdir repos/semafor_annotations
fi
if [ ! -d "./repos/sesame_annotations" ]; then
	mkdir repos/sesame_annotations
fi
if [ ! -d "./repos/semafor_aligned" ]; then
	mkdir repos/semafor_aligned
fi
if [ ! -d "./repos/sesame_aligned" ]; then
	mkdir repos/sesame_aligned
fi
