#!/bin/bash

# ===================================================
# Kled.io Go Codebase Rebranding Script
# ===================================================
# Purpose: Rebrand all Go code references from the original
#          GitHub repository to the new one
# ===================================================

# ===== Configuration =====
# Source (original) repository path
SOURCE_REPO="github.com/spectrumwebco/kled-beta"
# Destination (new) repository path
DEST_REPO="github.com/spectrumwebco/kled-beta"
# Name for backup directory
BACKUP_DIR="rebranding_backup_$(date +%Y%m%d_%H%M%S)"
# Root directory for the project
PROJECT_DIR="$(pwd)"
# Dry run mode (set to 1 to only show changes without applying them)
DRY_RUN=0

# ===== Color definitions =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===== Helper functions =====

# Print a message with timestamp
log() {
  echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Print a success message
success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Print an error message
error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Print a warning message
warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Create a backup of the project
create_backup() {
  log "Creating backup in ./$BACKUP_DIR"
  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Would create backup in ./$BACKUP_DIR"
    return
  fi

  mkdir -p "$BACKUP_DIR"
  cp -r "$PROJECT_DIR"/* "$BACKUP_DIR/"
  success "Backup created successfully in ./$BACKUP_DIR"
}

# ===== Main functions =====

# Update Git remote URL
update_git_remote() {
  log "Updating Git remote URL..."
  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Would execute: git remote set-url origin https://github.com/spectrumwebco/kled-beta.git"
    return
  fi

  if git remote set-url origin https://github.com/spectrumwebco/kled-beta.git; then
    success "Git remote URL updated successfully"
  else
    error "Failed to update Git remote URL"
    exit 1
  fi
}

# Find and replace import paths in Go files
update_go_imports() {
  log "Updating import paths in Go files..."
  local count=0

  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Would find all .go files and replace import paths"
    # Show a sample of files that would be affected
    find . -name "*.go" -type f | grep -v "/vendor/" | head -n 5
    return
  fi

  while IFS= read -r file; do
    if grep -q "$SOURCE_REPO" "$file"; then
      sed -i "s|$SOURCE_REPO|$DEST_REPO|g" "$file"
      count=$((count + 1))
      echo "  - Updated: $file"
    fi
  done < <(find . -name "*.go" -type f | grep -v "/vendor/")

  success "Updated import paths in $count Go files"
}

# Update module declarations in go.mod files
update_go_modules() {
  log "Updating module declarations in go.mod files..."
  local count=0

  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Would find all go.mod files and update module declarations"
    # Show a sample of files that would be affected
    find . -name "go.mod" -type f | head -n 5
    return
  fi

  while IFS= read -r file; do
    if grep -q "$SOURCE_REPO" "$file"; then
      # Replace in module declarations
      sed -i "s|module $SOURCE_REPO|module $DEST_REPO|g" "$file"
      # Replace in require statements
      sed -i "s|$SOURCE_REPO|$DEST_REPO|g" "$file"
      count=$((count + 1))
      echo "  - Updated: $file"
    fi
  done < <(find . -name "go.mod" -type f)

  success "Updated module declarations in $count go.mod files"
}

# Update references in markdown files
update_markdown() {
  log "Updating references in markdown files..."
  local count=0

  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Would find all .md files and update repository references"
    return
  fi

  while IFS= read -r file; do
    if grep -q "loft-sh/devpod" "$file"; then
      sed -i "s|loft-sh/devpod|spectrumwebco/kled-beta|g" "$file"
      count=$((count + 1))
      echo "  - Updated: $file"
    fi
  done < <(find . -name "*.md" -type f)

  success "Updated references in $count markdown files"
}

# Update references in configuration files
update_config_files() {
  log "Updating references in configuration files..."
  local count=0
  local files=".goreleaser.yml .github/workflows/*.yml .github/*.yml Makefile Dockerfile .travis.yml netlify.toml"

  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Would update references in configuration files"
    return
  fi

  for pattern in $files; do
    while IFS= read -r file; do
      if [ -f "$file" ] && grep -q "loft-sh/devpod" "$file"; then
        sed -i "s|loft-sh/devpod|spectrumwebco/kled-beta|g" "$file"
        count=$((count + 1))
        echo "  - Updated: $file"
      fi
    done < <(find . -path "./$pattern" -type f 2>/dev/null)
  done

  success "Updated references in $count configuration files"
}

# Run go mod tidy on all modules
run_go_mod_tidy() {
  log "Running go mod tidy on all modules..."
  local count=0

  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Would run go mod tidy on all modules"
    return
  fi

  while IFS= read -r dir; do
    log "  Running go mod tidy in: $dir"
    (cd "$dir" && go mod tidy) || warning "Failed to run go mod tidy in $dir"
    count=$((count + 1))
  done < <(find . -name "go.mod" -type f -exec dirname {} \;)

  success "Ran go mod tidy on $count modules"
}

# Handle additional cases like string literals and comments
update_additional_references() {
  log "Updating additional references (string literals, comments, etc.)..."
  local count=0

  if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Would update additional references"
    return
  fi

  # Check for string literals like "github.com/spectrumwebco/kled-beta"
  while IFS= read -r file; do
    if grep -q "\"$SOURCE_REPO" "$file" || grep -q "'$SOURCE_REPO" "$file"; then
      sed -i "s|\"$SOURCE_REPO|\"$DEST_REPO|g" "$file"
      sed -i "s|'$SOURCE_REPO|'$DEST_REPO|g" "$file"
      count=$((count + 1))
      echo "  - Updated string literal in: $file"
    fi
  done < <(find . -type f -not -path "*/\.*" -not -path "*/vendor/*" -not -path "*/$BACKUP_DIR/*")

  # Look for devpod-specific URLs and patterns
  while IFS= read -r file; do
    if grep -q "spectrumwebco.github.io/kled-beta" "$file" || grep -q "raw.githubusercontent.com/spectrumwebco/kled-beta" "$file"; then
      sed -i "s|spectrumwebco.github.io/kled-beta|spectrumwebco.github.io/kled-beta|g" "$file"
      sed -i "s|raw.githubusercontent.com/spectrumwebco/kled-beta|raw.githubusercontent.com/spectrumwebco/kled-beta|g" "$file"
      count=$((count + 1))
      echo "  - Updated URL in: $file"
    fi
  done < <(find . -type f -not -path "*/\.*" -not -path "*/vendor/*" -not -path "*/$BACKUP_DIR/*")

  success "Updated $count additional references"
}

# Verify the changes made
verify_changes() {
  log "Verifying changes..."

  # Check if there are still references to the original repository
  remaining=$(grep -r --include="*.go" --include="go.mod" "$SOURCE_REPO" . | wc -l)

  if [ "$remaining" -gt 0 ]; then
    warning "Found $remaining remaining references to $SOURCE_REPO"
    log "You may need to manually review these files:"
    grep -r --include="*.go" --include="go.mod" "$SOURCE_REPO" . | head -n 10
    if [ "$(grep -r --include="*.go" --include="go.mod" "$SOURCE_REPO" . | wc -l)" -gt 10 ]; then
      log "... and more. Run 'grep -r --include=\"*.go\" --include=\"go.mod\" \"$SOURCE_REPO\" .' to see all."
    fi
  else
    success "No remaining references to $SOURCE_REPO found in Go files and go.mod files"
  fi

  # Check for loft-sh/devpod references in general
  remaining=$(grep -r "loft-sh/devpod" . --include="*.*" | wc -l)
  if [ "$remaining" -gt 0 ]; then
    warning "Found $remaining additional references to 'loft-sh/devpod'"
    log "You may need to manually review these files:"
    grep -r "loft-sh/devpod" . --include="*.*" | head -n 10
    if [ "$(grep -r "loft-sh/devpod" . --include="*.*" | wc -l)" -gt 10 ]; then
      log "... and more. Run 'grep -r \"loft-sh/devpod\" .' to see all."
    fi
  else
    success "No remaining references to 'loft-sh/devpod' found in general files"
  fi
}

# ===== Main script execution =====

# Print banner
echo -e "${GREEN}========================================================"
echo -e "      Kled.io Go Codebase Rebranding Script"
echo -e "========================================================"
echo -e "${NC}"

# Check for required commands
for cmd in git find grep sed; do
  if ! command_exists "$cmd"; then
    error "Required command '$cmd' not found. Please install it and try again."
    exit 1
  fi
done

# Check if we're in the right directory
if [ ! -d .git ]; then
  error "This doesn't appear to be a git repository. Please run from the project root."
  exit 1
fi

# Confirm with the user
echo -e "This script will rebrand the Go codebase from:"
echo -e "  ${YELLOW}$SOURCE_REPO${NC}"
echo -e "to:"
echo -e "  ${GREEN}$DEST_REPO${NC}"
echo -e ""
echo -e "Current directory: ${BLUE}$PROJECT_DIR${NC}"
echo -e ""

if [ "$DRY_RUN" -eq 1 ]; then
  echo -e "${YELLOW}Running in DRY RUN mode. No changes will be applied.${NC}"
else
  echo -e "${YELLOW}WARNING: This will modify your files in place.${NC}"
  echo -e "A backup will be created in: $BACKUP_DIR"
  echo -e ""
  read -p "Do you want to proceed? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Operation cancelled by user"
    exit 0
  fi

  # Create backup
  create_backup
fi

# Execute the rebranding steps
update_git_remote
update_go_imports
update_go_modules
update_markdown
update_config_files
update_additional_references
run_go_mod_tidy
verify_changes

# Print completion message
if [ "$DRY_RUN" -eq 1 ]; then
  log "Dry run completed. No changes were made."
  log "To apply changes, run the script with DRY_RUN=0"
else
  success "Rebranding completed successfully!"
  log "Next steps:"
  log "1. Review the changes with 'git diff'"
  log "2. Build and test your application"
  log "3. Commit and push the changes to your new repository"
  log "   git add ."
  log "   git commit -m \"Rebrand from loft-sh/devpod to spectrumwebco/kled-beta\""
  log "   git push -u origin main"
fi

echo -e "${GREEN}========================================================"
echo -e "      Rebranding Process Complete"
echo -e "========================================================${NC}"
