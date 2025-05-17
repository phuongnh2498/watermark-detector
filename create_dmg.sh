#!/bin/bash

# Script to create a DMG file for the WatermarkDetector application
# This script uses the built-in hdiutil command on macOS

# Set variables
APP_NAME="WatermarkDetector"
DMG_NAME="${APP_NAME}_Installer"
APP_PATH="dist/${APP_NAME}.app"
DMG_PATH="dist/${DMG_NAME}.dmg"
VOLUME_NAME="${APP_NAME} Installer"

# Check if the app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: $APP_PATH does not exist. Please build the app first."
    exit 1
fi

# Remove any existing DMG file
if [ -f "$DMG_PATH" ]; then
    echo "Removing existing DMG file..."
    rm "$DMG_PATH"
fi

# Create the DMG file directly from the app
echo "Creating DMG file..."
hdiutil create -volname "$VOLUME_NAME" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"

echo "DMG file created successfully: $DMG_PATH"
echo "You can distribute this file to other macOS users."
