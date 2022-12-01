#!/bin/bash
echo "Script for doing all available tests and executing program"

echo "Getting python3 executable loc"
python_exec_loc=$(which python3)
if [ $? -eq 0 ]; then echo "All good bruv"; else echo "Master, I've run into a problem while trying to find your python exec location :("; exit 1; fi
echo "$python_exec_loc"
echo "------------------------" 

echo "------------------------"
if test -f "test_worker.py"; then
    echo "test found - test_worker"
    $python_exec_loc test_worker.py
else 
    echo "Missing test file..."
fi
echo "------------------------"

if test -f "test_config.py"; then
    echo "test found - test_config"
    $python_exec_loc test_config.py
else 
    echo "Missing test file..."
fi
echo "------------------------"

if test -f "my_test.py"; then
    echo "test found - my_test"
    $python_exec_loc my_test.py
else 
    echo "Missing test file..."
fi
echo "------------------------"

echo "Okay, sir. You're good to go! to start the program - execute this:"
echo "$python_exec_loc naked.py" 