#!/bin/bash
set -e

# Create logs directory
mkdir -p /app/logs

# Create recordings directory
mkdir -p /app/recordings

# Install Node.js and PM2 if not already installed
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

if ! command -v pm2 &> /dev/null; then
    echo "Installing PM2..."
    npm install -g pm2
fi

# Start the application with PM2
echo "Starting Motion Detection System with PM2..."
pm2-runtime start ecosystem.config.js --env production
