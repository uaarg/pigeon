#!/bin/bash 
#Written by Arshad Husain <husain3@ualberta.ca>
currentTime=$(date +"%b-%d-%Y|%T")
FILE=~/data/captured
#echo $1
echo "$currentTime"

if [ "$(ls -A $FILE)" ];
then
	#echo "Folder $FILE is NOT empty"
	mkdir ~/data/archive/Archived@"$currentTime"
	mv ~/data/captured/*.jpg ~/data/archive/Archived@"$currentTime"
	mv ~/data/captured/*.txt ~/data/archive/Archived@"$currentTime"

#else
	#echo "Folder $FILE is empty"
fi
#add if statement to check for files

