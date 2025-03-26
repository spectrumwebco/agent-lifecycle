#!/bin/bash

# Build the Kled CLI
echo "Building Kled CLI..."
cd cmd/kled
go mod tidy
go build -o ../../bin/kled
cd ../..

if [ -f ./bin/kled ]; then
    echo "Kled CLI built successfully!"
    echo "Testing the CLI..."
    ./bin/kled version
    echo ""

    echo "Testing workspace commands..."
    ./bin/kled workspace list
    echo ""

    echo "Testing GPU support..."
    ./bin/kled gpu info
    echo ""

    echo "Testing MCP integration..."
    ./bin/kled mcp status
    echo ""

    echo "Testing interpreter..."
    ./bin/kled interpreter status
    echo ""
else
    echo "Failed to build Kled CLI"
    exit 1
fi

echo "Build complete!"
