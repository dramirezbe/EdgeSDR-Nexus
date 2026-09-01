#!/bin/bash

################################################################################
# Backup Script for ANE Production Server
# Creates compressed backups of frontend, backend, and postprocesamiento
# Then removes the original directories
################################################################################

set -euo pipefail

# Configuration
BACKUP_DIR="${1:-.}"  # Default to current directory if not specified
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${BACKUP_DIR}/backup-${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

# Verify we're in the right directory
if [ ! -d "${BACKUP_DIR}/backend" ] && [ ! -d "${BACKUP_DIR}/frontend" ] && [ ! -d "${BACKUP_DIR}/postprocesamiento" ]; then
    log_error "No backend, frontend, or postprocesamiento directories found in ${BACKUP_DIR}"
    exit 1
fi

log "Starting backup process..."
log "Backup directory: ${BACKUP_DIR}"
log "Timestamp: ${TIMESTAMP}"

# Array to track backup status
declare -a BACKED_UP_DIRS=()
declare -a BACKUP_SIZES=()
declare -a FAILED_DIRS=()

# Function to backup and delete directory
backup_directory() {
    local dir_name=$1
    local dir_path="${BACKUP_DIR}/${dir_name}"
    
    if [ ! -d "$dir_path" ]; then
        log_warning "Directory ${dir_name} not found, skipping..."
        return 0
    fi
    
    log "Backing up ${dir_name}..."
    
    local backup_file="${BACKUP_DIR}/${dir_name}-${TIMESTAMP}.tar.gz"
    local backup_folder="${BACKUP_DIR}/${dir_name}.backup-${TIMESTAMP}"
    
    # Create compressed backup
    if tar -czf "$backup_file" -C "$BACKUP_DIR" "$dir_name" 2>>"$LOG_FILE"; then
        local file_size=$(du -h "$backup_file" | cut -f1)
        log_success "Created backup: $(basename $backup_file) (${file_size})"
        BACKED_UP_DIRS+=("$dir_name")
        BACKUP_SIZES+=("$file_size")
        
        # Optional: Create backup folder reference (uncomment if desired)
        # mkdir -p "$backup_folder"
        # cp -r "$dir_path"/* "$backup_folder/" 2>>"$LOG_FILE"
        # log "Created backup folder: $(basename $backup_folder)"
        
        # Delete original directory
        log "Removing original directory: ${dir_name}..."
        if rm -rf "$dir_path"; then
            log_success "Deleted original directory: ${dir_name}"
        else
            log_error "Failed to delete directory: ${dir_name}"
            FAILED_DIRS+=("$dir_name")
        fi
    else
        log_error "Failed to create backup for ${dir_name}"
        FAILED_DIRS+=("$dir_name")
    fi
}

# Backup each component
backup_directory "backend"
backup_directory "frontend"
backup_directory "postprocesamiento"

# Summary
log "==============================================="
log "Backup Summary"
log "==============================================="

if [ ${#BACKED_UP_DIRS[@]} -gt 0 ]; then
    log_success "Backed up components:"
    for i in "${!BACKED_UP_DIRS[@]}"; do
        log "  - ${BACKED_UP_DIRS[$i]} (${BACKUP_SIZES[$i]})"
    done
fi

if [ ${#FAILED_DIRS[@]} -gt 0 ]; then
    log_error "Failed to backup/delete:"
    for dir in "${FAILED_DIRS[@]}"; do
        log_error "  - $dir"
    done
    exit 1
fi

log_success "Backup process completed successfully!"
log "Log file: ${LOG_FILE}"
