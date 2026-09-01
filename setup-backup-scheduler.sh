#!/bin/bash

################################################################################
# Backup Scheduler and Retention Manager
# Sets up cron jobs for automatic backups and cleans old backups
################################################################################

set -euo pipefail

# Configuration
BACKUP_DIR="${1:-.}"
BACKUP_SCRIPT="${BACKUP_DIR}/backup-production.sh"
RETENTION_DAYS="${2:-30}"  # Keep backups for 30 days by default
CRON_SCHEDULE="${3:-0 2 * * *}"  # Default: Daily at 2 AM

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== ANE Backup Scheduler ===${NC}"
echo "Backup directory: $BACKUP_DIR"
echo "Backup script: $BACKUP_SCRIPT"
echo "Retention period: $RETENTION_DAYS days"
echo "Cron schedule: $CRON_SCHEDULE"
echo ""

# Validate backup script exists and is executable
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}Error: Backup script not found at $BACKUP_SCRIPT${NC}"
    exit 1
fi

if [ ! -x "$BACKUP_SCRIPT" ]; then
    echo -e "${YELLOW}Making backup script executable...${NC}"
    chmod +x "$BACKUP_SCRIPT"
fi

# Create retention cleanup script
RETENTION_SCRIPT="${BACKUP_DIR}/cleanup-old-backups.sh"
cat > "$RETENTION_SCRIPT" << 'RETENTION_EOF'
#!/bin/bash

# Cleanup old backup files and directories
# Usage: cleanup-old-backups.sh <backup_dir> [retention_days]

BACKUP_DIR="${1:-.}"
RETENTION_DAYS="${2:-30}"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "Cleaning up backups older than $RETENTION_DAYS days in $BACKUP_DIR..."

# Find and remove old backup files (*.tar.gz)
find "$BACKUP_DIR" -maxdepth 1 -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -print0 | \
while IFS= read -r -d '' file; do
    echo "Removing: $file"
    rm -f "$file"
done

# Find and remove old backup directories (*.backup-*)
find "$BACKUP_DIR" -maxdepth 1 -name "*.backup-*" -type d -mtime +$RETENTION_DAYS -print0 | \
while IFS= read -r -d '' dir; do
    echo "Removing: $dir"
    rm -rf "$dir"
done

echo "Cleanup completed!"
RETENTION_EOF

chmod +x "$RETENTION_SCRIPT"
echo -e "${GREEN}Created cleanup script: $RETENTION_SCRIPT${NC}"

# Display usage instructions
echo ""
echo -e "${GREEN}=== Setup Instructions ===${NC}"
echo ""
echo "1. Manual backup execution:"
echo "   cd $BACKUP_DIR"
echo "   ./backup-production.sh"
echo ""
echo "2. Schedule automatic backups with cron:"
echo "   Run: crontab -e"
echo "   Add this line for daily backups at 2 AM:"
echo "   $CRON_SCHEDULE cd $BACKUP_DIR && ./backup-production.sh >> backup-cron.log 2>&1"
echo ""
echo "3. Manual cleanup of old backups:"
echo "   $RETENTION_SCRIPT $BACKUP_DIR $RETENTION_DAYS"
echo ""
echo "4. Schedule automatic cleanup with cron:"
echo "   Add this line for weekly cleanup (Sunday at 3 AM):"
echo "   0 3 * * 0 $RETENTION_SCRIPT $BACKUP_DIR $RETENTION_DAYS >> cleanup-cron.log 2>&1"
echo ""
