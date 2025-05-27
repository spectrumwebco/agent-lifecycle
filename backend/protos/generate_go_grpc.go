package protos

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
)

func GenerateGoGRPC() error {
	cwd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("failed to get current working directory: %v", err)
	}

	protoFile := filepath.Join(cwd, "agent.proto")

	if _, err := os.Stat(protoFile); os.IsNotExist(err) {
		return fmt.Errorf("proto file not found: %s", protoFile)
	}

	outputDir := filepath.Join(cwd, "generated", "go")
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %v", err)
	}

	cmd := exec.Command(
		"protoc",
		"--go_out="+outputDir,
		"--go-grpc_out="+outputDir,
		"--go_opt=paths=source_relative",
		"--go-grpc_opt=paths=source_relative",
		protoFile,
	)

	cmd.Dir = cwd

	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("failed to generate Go gRPC code: %v\nOutput: %s", err, output)
	}

	log.Printf("Successfully generated Go gRPC code in %s", outputDir)
	return nil
}

func main() {
	if err := GenerateGoGRPC(); err != nil {
		log.Fatalf("Error: %v", err)
	}
}
