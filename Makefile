# Kled.io Makefile
# Build and deployment targets for Kled.io desktop and CLI

KLED_VERSION := 1.0.0
GO_BUILD_FLAGS := -ldflags="-X main.Version=$(KLED_VERSION)"
GO_FILES := $(shell find cmd -name "*.go")

.PHONY: all clean cli desktop build test docker

all: cli desktop

# Build the CLI
cli: bin/kled

bin/kled: $(GO_FILES)
	@echo "Building Kled CLI..."
	@cd cmd/kled && go mod tidy
	@cd cmd/kled && go build $(GO_BUILD_FLAGS) -o ../../bin/kled
	@echo "Kled CLI built successfully!"

# Run the CLI
run-cli: bin/kled
	@./bin/kled

# Build the desktop app
desktop:
	@echo "Building Kled Desktop..."
	@cd desktop && yarn install
	@cd desktop && yarn build
	@echo "Kled Desktop built successfully!"

# Package the desktop app
package-desktop: desktop
	@echo "Packaging Kled Desktop..."
	@cd desktop && yarn tauri build
	@echo "Kled Desktop packaged successfully!"

# Build the Docker image
docker:
	@echo "Building Docker image..."
	@docker build -t spectrumwebco/kled:$(KLED_VERSION) .
	@echo "Docker image built successfully!"

# Run tests
test:
	@echo "Running tests..."
	@cd cmd/kled && go test ./...
	@cd desktop && yarn test
	@echo "Tests completed successfully!"

# Run the CLI with specific commands
test-cli: bin/kled
	@echo "Testing Kled CLI..."
	@./bin/kled version
	@./bin/kled workspace list
	@./bin/kled gpu info
	@./bin/kled mcp status
	@./bin/kled interpreter status

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf bin/*
	@cd desktop && yarn clean
	@echo "Clean completed successfully!"

# Show help
help:
	@echo "Kled.io Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all           - Build CLI and desktop app"
	@echo "  cli           - Build the CLI"
	@echo "  desktop       - Build the desktop app"
	@echo "  package-desktop - Package the desktop app for distribution"
	@echo "  docker        - Build the Docker image"
	@echo "  test          - Run tests"
	@echo "  test-cli      - Test the CLI commands"
	@echo "  clean         - Clean build artifacts"
	@echo "  help          - Show this help message"
