#!/bin/bash
# Publish evoid-scheduler to PyPI

WHEEL="/home/ali/Templates/Project/python/evoid-plugins/dist/evoid_scheduler-1.0.0-py3-none-any.whl"

if [ ! -f "$WHEEL" ]; then
    echo "Wheel not found. Building..."
    cd /home/ali/Templates/Project/python/evoid-plugins/packages/evoid-scheduler
    uv build
fi

echo "Publishing evoid-scheduler to PyPI..."
uv publish "$WHEEL"

if [ $? -eq 0 ]; then
    echo "Done! https://pypi.org/project/evoid-scheduler/"
else
    echo "Failed. Check ~/.pypirc token."
fi
