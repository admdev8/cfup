#!/bin/sh

touch /var/log/cfup.log

while true; do
	/opt/cfup/cfup.py update-entries &> /var/log/cfup.log
	sleep 5m
done
