# Kled.io Makefile

# Go related variables
GOBASE := $(shell pwd)
GOBIN := $(GOBASE)/bin
GO := go

# Binary names
CLI_NAME := kled
CLI_BIN := $(GOBIN)/$(CLI_NAME)

# Main packages
CLI_PACKAGE := ./cmd/kled

# SpacetimeDB related variables
SPACETIME_SERVER_DIR := desktop/server
SPACETIME_CMD := spacetime

# Version information
VERSION := 0.1.0
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_TIME := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build flags
LDFLAGS := -ldflags "-X main.Version=$(VERSION) -X main.Commit=$(COMMIT) -X main.BuildTime=$(BUILD_TIME)"

.PHONY: all clean build build-cli build-server test fmt lint run-cli spacetime-init

# Default target
all: clean build test

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(GOBIN)
	@mkdir -p $(GOBIN)

# Build everything
build: build-cli build-server

# Build the CLI
build-cli:
	@echo "Building Kled.io CLI..."
	@mkdir -p $(GOBIN)
	@cd $(GOBASE) && $(GO) build $(LDFLAGS) -o $(CLI_BIN) $(CLI_PACKAGE)
	@echo "CLI built successfully: $(CLI_BIN)"

# Build the SpacetimeDB server
build-server:
	@echo "Building SpacetimeDB server..."
	@cd $(SPACETIME_SERVER_DIR) && cargo build
	@echo "SpacetimeDB server built successfully"

# Run tests
test: test-cli test-server

# Test the CLI
test-cli:
	@echo "Testing Kled.io CLI..."
	@cd $(GOBASE) && $(GO) test -v ./...

# Test the SpacetimeDB server
test-server:
	@echo "Testing SpacetimeDB server..."
	@cd $(SPACETIME_SERVER_DIR) && cargo test

# Run the CLI
run-cli:
	@echo "Running Kled.io CLI..."
	@$(CLI_BIN) $(ARGS)

# Initialize SpacetimeDB
spacetime-init:
	@echo "Initializing SpacetimeDB..."
	@$(SPACETIME_CMD) init --lang rust server

# Test workspace resources
test-resources:
	@echo "Testing workspace resources..."
	@$(CLI_BIN) test resources

# Test CUDA support
test-cuda:
	@echo "Testing CUDA support..."
	@$(CLI_BIN) test cuda

# Test Code Interpreter API
test-interpreter:
	@echo "Testing Code Interpreter API..."
	@$(CLI_BIN) test interpreter
