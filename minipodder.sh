#!/bin/bash
#
# Simple podcast client which keeps track of downloaded files
#
# Dependencies: curl, libxslt
set +o posix
BASEDIR="$(dirname "$(realpath "$0")")"

##############################################################################

# path to text file with line separted list of feed urls
FEED_FILE="${BASEDIR}/feeds.txt"

# path to folder where the downloaded files are stored
DOWNLOAD_DIR="${BASEDIR}/PODCASTS"

# maximum number of files to download from a feed
MAX_FILES=1

##############################################################################

LOG_FILE="${DOWNLOAD_DIR}/podcasts.m3u"
BAD_CHARS="!#$^&=+{}[]:;\"\\'<>?|"
CURL_ARGS="--location --continue-at - --progress-bar"

##############################################################################

function parse_feed {
    xsltproc - "$1" <<< '<?xml version="1.0"?>
        <stylesheet version="1.0"
        	xmlns="http://www.w3.org/1999/XSL/Transform">
        	<output method="text"/>
        	<template match="/">
        		<apply-templates select="/rss/channel/item/enclosure"/>
        	</template>
        	<template match="enclosure">
        		<value-of select="@url"/><text>&#10;</text>
        	</template>
        </stylesheet>'
}

function filename_from_url {
    basename "$1" | cut -d'?' -f1 | tr "$BAD_CHARS" "-"
}

function prepend_to_logfile {
    local tmp_logfile=$(mktemp "${LOG_FILE}.XXXXX")
    trap 'rm "$tmp_logfile"' INT TERM EXIT

    echo "$1" | cat - "$LOG_FILE" > "$tmp_logfile"
    mv "$tmp_logfile" "$LOG_FILE"
    trap - INT TERM EXIT
}

##############################################################################

: >> "${LOG_FILE}"

while read feed ; do
    echo "Parsing feed: $feed"
    while read item ; do
        filename=$(filename_from_url "$item")
        filepath="${DOWNLOAD_DIR}/$filename"

        grep -q -F "$filename" "$LOG_FILE" && continue 2

        echo "Downloading \"${filename}\"..."
        curl $CURL_ARGS -o "$filepath" "$item" || break 2

        prepend_to_logfile "$filename"
    done < <(parse_feed "$feed" | head -$MAX_FILES)
done <"$FEED_FILE"
