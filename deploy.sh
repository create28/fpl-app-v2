#!/bin/bash

# Create necessary directories
mkdir -p cache
mkdir -p logs

# Install required Python packages
pip install -r requirements.txt

# Start the server with nohup to keep it running after SSH session ends
nohup python fetch_fpl_data.py > logs/app.log 2>&1 &

# Print the process ID
echo "Server started with PID: $!"
echo "Check logs/app.log for server output" 