#!/usr/bin/env bash

# Directory containing JSON files
DIR="examples"

# Endpoint
URL="http://127.0.0.1:8001/api/questions/generate"

# Check if directory exists
if [ ! -d "$DIR" ]; then
  echo "Error: Directory '$DIR' not found."
  exit 1
fi

# Loop through all JSON files in the directory
for FILE in "$DIR"/*.json; do
  if [ -f "$FILE" ]; then
    echo "Processing: $FILE"
    curl -s -X POST "$URL" \
      -H "Content-Type: application/json" \
      -d @"$FILE"
    echo -e "\n--- Done with $FILE ---\n"
  else
    echo "No JSON files found in $DIR"
    exit 1
  fi
done
