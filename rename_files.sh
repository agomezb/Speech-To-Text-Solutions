#!/bin/bash

# Script to rename files in a folder with a prefix and sequential numbering
# Usage: ./rename_files.sh <folder_path> <prefix>

# Check if correct number of arguments provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <folder_path> <prefix>"
    echo "Example: $0 ./audio recording"
    exit 1
fi

FOLDER="$1"
PREFIX="$2"

# Check if folder exists
if [ ! -d "$FOLDER" ]; then
    echo "Error: Folder '$FOLDER' does not exist"
    exit 1
fi

# Check if folder is empty
file_count=$(find "$FOLDER" -maxdepth 1 -type f | wc -l)
if [ "$file_count" -eq 0 ]; then
    echo "Error: No files found in folder '$FOLDER'"
    exit 1
fi

echo "Found $file_count files in '$FOLDER'"
echo "Renaming files with prefix '$PREFIX'..."
echo ""

# Counter for sequential numbering
counter=1

# Get all files sorted alphabetically and iterate
# Using a while loop with process substitution
while IFS= read -r file; do
    # Get the file extension
    extension="${file##*.}"
    
    # Get the directory path
    dir=$(dirname "$file")
    
    # Check if file has an extension
    if [ "$extension" = "$(basename "$file")" ]; then
        # No extension found
        new_name="${dir}/${PREFIX}_${counter}"
    else
        # Extension found
        new_name="${dir}/${PREFIX}_${counter}.${extension}"
    fi
    
    # Only rename if the new name is different
    if [ "$file" != "$new_name" ]; then
        echo "Renaming: $(basename "$file") -> $(basename "$new_name")"
        mv "$file" "$new_name"
    else
        echo "Skipping: $(basename "$file") (already has correct name)"
    fi
    
    counter=$((counter + 1))
done < <(find "$FOLDER" -maxdepth 1 -type f | sort -V)

echo ""
echo "Renaming complete!"

