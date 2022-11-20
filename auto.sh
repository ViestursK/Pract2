#!/bin/bash
echo "Script for doing all available tests and executing program"
echo "------------------------"
if test -f "test_worker.py"; then
    echo "test found"
else 
    echo "Missing test file..."
fi
echo "------------------------"

if test -f "test_config.py"; then
    echo "test found"
else 
    echo "Missing test file..."
fi
echo "------------------------"

if test -f "my_test.py"; then
    echo "test found"
else 
    echo "Missing test file..."
fi
echo "------------------------"

py_exec_loc=$(which python3)
if [$? -eq 0]; then echo "All good bruv"; else echo "Master, I've run into a problem while trying to find your python exec location :("
echo "$py_exec_loc"
echo "------------------------"

echo "Okay, sir. You're good to go! to start the program - execute this:"
echo "$py_exec_loc naked.py" 