#!/bin/bash

FILE=$1
KEY=$2
TYPE=$3

aws s3 cp $FILE s3://assets.solusorbis.com/$KEY --cache-control 'public, max-age=604800, immutable' --content-type $TYPE