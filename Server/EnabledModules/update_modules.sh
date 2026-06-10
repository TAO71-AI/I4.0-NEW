#!/bin/bash
git --version &>/dev/null

if [ $? -ne 0 ]; then
    echo "Error: Git is not installed."
    exit 1
fi

for dir in */; do
    if [ -d "$dir" ]; then
        if [ -d "$dir/.git" ]; then
            echo "Updating '$dir'..."

            cd "$dir" || continue
            git pull
            cd ..
        else
            echo "'.git' dir not found. Skipping."
        fi
    fi
done