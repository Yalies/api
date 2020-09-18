#!/usr/bin/env bash

rm -rf .git/hooks
echo "Symlinking new hooks..."
ln -s ../hooks .git/hooks
echo "Done."
