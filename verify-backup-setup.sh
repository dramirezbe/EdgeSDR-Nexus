#!/bin/bash

################################################################################
# Verify Backup System Setup
# Checks that all backup scripts are properly configured and ready to run
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="${1:-.}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ANE Backup System Verification                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check 1: Verify scripts exist
echo -e "${YELLOW}[1/7]${NC} Checking for backup scripts..."
for script in "backup-production.sh" "cleanup-old-backups.sh" "install-backup-production.sh"; do
    if [ -f "$BACKUP_DIR/$script" ]; then
        echo -e "${GREEN}✓${NC} $script"
    else
        echo -e "${RED}✗${NC} $script NOT FOUND"
    fi
done
echo ""

# Check 2: Verify scripts are executable
echo -e "${YELLOW}[2/7]${NC} Checking script permissions..."
for script in "backup-production.sh" "cleanup-old-backups.sh"; do
    script_path="$BACKUP_DIR/$script"
    if [ -x "$script_path" ]; then
        echo -e "${GREEN}✓${NC} $script is executable"
    else
        echo -e "${RED}✗${NC} $script is NOT executable"
    fi
done
echo ""

# Check 3: Verify components exist
echo -e "${YELLOW}[3/7]${NC} Checking for components to backup..."
components_found=0
for component in "backend" "frontend" "postprocesamiento"; do
    if [ -d "$BACKUP_DIR/$component" ]; then
        size=$(du -sh "$BACKUP_DIR/$component" | cut -f1)
        echo -e "${GREEN}✓${NC} $component ($size)"
        ((components_found++))
    else
        echo -e "${YELLOW}○${NC} $component not found (expected if already backed up)"
    fi
done

if [ $components_found -eq 0 ]; then
    echo -e "${YELLOW}Note: No components found. They may have been backed up already.${NC}"
fi
echo ""

# Check 4: Check for existing backups
echo -e "${YELLOW}[4/7]${NC} Checking for existing backups..."
backup_count=$(find "$BACKUP_DIR" -maxdepth 1 -name "*.tar.gz" -type f 2>/dev/null | wc -l)
backup_dir_count=$(find "$BACKUP_DIR" -maxdepth 1 -name "*.backup-*" -type d 2>/dev/null | wc -l)
total_backup_size=$(find "$BACKUP_DIR" -maxdepth 1 -name "*.tar.gz" -type f -exec du -c {} + 2>/dev/null | tail -1 | cut -f1)

echo -e "${GREEN}✓${NC} Backup files: $backup_count"
echo -e "${GREEN}✓${NC} Backup directories: $backup_dir_count"
if [ "$total_backup_size" -gt 0 ]; then
    total_size_formatted=$(numfmt --to=iec $total_backup_size 2>/dev/null || echo "$total_backup_size bytes")
    echo -e "${GREEN}✓${NC} Total backup size: $total_size_formatted"
fi
echo ""

# Check 5: Disk space
echo -e "${YELLOW}[5/7]${NC} Checking disk space..."
available=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
available_formatted=$(numfmt --to=iec $((available * 1024)) 2>/dev/null || echo "$available KB")
echo -e "${GREEN}✓${NC} Available space: $available_formatted"
if [ "$available" -lt 100000 ]; then  # Less than 100MB
    echo -e "${RED}⚠${NC}  WARNING: Low disk space!"
fi
echo ""

# Check 6: Cron configuration
echo -e "${YELLOW}[6/7]${NC} Checking cron configuration..."
if crontab -l 2>/dev/null | grep -q "backup-production.sh"; then
    echo -e "${GREEN}✓${NC} Backup cron job found"
    crontab -l 2>/dev/null | grep "backup-production.sh" | sed 's/^/   /'
else
    echo -e "${YELLOW}○${NC} No backup cron job configured"
fi

if crontab -l 2>/dev/null | grep -q "cleanup-old-backups.sh"; then
    echo -e "${GREEN}✓${NC} Cleanup cron job found"
else
    echo -e "${YELLOW}○${NC} No cleanup cron job configured"
fi
echo ""

# Check 7: Systemd timer
echo -e "${YELLOW}[7/7]${NC} Checking systemd timer..."
if systemctl is-enabled ane-backup.timer &>/dev/null; then
    timer_status=$(systemctl is-active ane-backup.timer)
    echo -e "${GREEN}✓${NC} Systemd timer found (status: $timer_status)"
else
    echo -e "${YELLOW}○${NC} Systemd timer not configured"
fi
echo ""

# Summary and recommendations
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Summary and Recommendations                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ $components_found -gt 0 ]; then
    echo -e "${YELLOW}Ready to backup${NC}:"
    echo "  Run: $BACKUP_DIR/backup-production.sh"
    echo ""
else
    echo -e "${YELLOW}Backups have already been performed${NC}."
    echo "  To restore: tar -xzf $BACKUP_DIR/[component]-[timestamp].tar.gz"
    echo ""
fi

if ! crontab -l 2>/dev/null | grep -q "backup-production.sh"; then
    echo -e "${YELLOW}To automate backups, run${NC}:"
    echo "  sudo $BACKUP_DIR/install-backup-production.sh $BACKUP_DIR"
    echo ""
fi

echo -e "${GREEN}Verification complete!${NC}"
echo ""
