#!/bin/bash

DBNAME=$1
PRODNAME="kiosk"

if [[ $# -eq 0 ]]; then
	DBNAME="kiosk_test_"
	DBNAME+=$(date +%s)
elif [[ $# -eq 1 ]]; then
	if [[ "$DBNAME" = "$PRODNAME" ]]; then
		echo "!!! WARNING !!!"
		echo "'$DBNAME' is the production database name!"
		echo "This will PERMAMENTLY DESTROY this database if it exists!"
		read -p "Continue? " -n 1 -r
		echo
		if [[ ! $REPLY =~ ^[Yy]$ ]]; then
			echo "Aborting."
			exit 1
		fi
	fi
else
	echo "Usage: ./create_database.sh dbname"
	echo "	If dbname is not given, creates unique new test db."
	exit 1
fi 

echo "Using dbname '${DBNAME}'."

IFS='%'
SQL="$(sed -e "s/%DBNAME%/$DBNAME/g" ./database.schema)"
unset IFS

echo "$SQL" | mysql -u root -p