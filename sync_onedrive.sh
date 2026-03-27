#!/bin/bash
# Sync wedding photos to OneDrive using rclone.
# Run manually or via cron: */10 * * * * /path/to/sync_onedrive.sh
#
# Setup:
#   1. Install rclone: curl https://rclone.org/install.sh | sudo bash
#   2. Configure OneDrive: rclone config  (follow the prompts to add "onedrive")
#   3. Test: rclone ls onedrive:
#   4. Add to cron: crontab -e  ->  */10 * * * * /home/pi/PhotoUpload/sync_onedrive.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.env" 2>/dev/null || true

PHOTO_DIR="${UPLOAD_FOLDER:-$SCRIPT_DIR/photos}"
REMOTE="${RCLONE_REMOTE:-onedrive}"
DEST="${RCLONE_DEST_PATH:-WeddingPhotos}"
LOG_FILE="$SCRIPT_DIR/sync.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting sync..." >> "$LOG_FILE"

rclone copy "$PHOTO_DIR" "$REMOTE:$DEST" \
    --exclude "thumbs/**" \
    --log-file "$LOG_FILE" \
    --log-level INFO \
    --transfers 4 \
    --checkers 8

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync complete." >> "$LOG_FILE"
