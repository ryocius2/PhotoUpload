#!/bin/bash
# Sync wedding photos to Windows PC via scp.
# Runs via cron: */10 * * * * /home/pi/PhotoUpload/sync_photos.sh
#
# Photos land in OneDrive/Pictures/WeddingPhotos on the PC,
# which auto-syncs to OneDrive cloud.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.env" 2>/dev/null || true

PHOTO_DIR="${UPLOAD_FOLDER:-$SCRIPT_DIR/photos}"
LOG_FILE="$SCRIPT_DIR/sync.log"

DEST_USER="ryoci"
DEST_HOST="192.168.4.35"
DEST_PATH="/C/Users/ryoci/OneDrive/Pictures/WeddingPhotos/"
SSH_KEY="/home/pi/.ssh/id_ed25519"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting sync..." >> "$LOG_FILE"

rsync -avz --exclude 'thumbs/' --exclude 'lost+found/' \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    "$PHOTO_DIR/" \
    "$DEST_USER@$DEST_HOST:$DEST_PATH" \
    >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync complete." >> "$LOG_FILE"
