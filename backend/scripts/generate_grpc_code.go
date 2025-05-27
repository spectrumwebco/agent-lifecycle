package scripts

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var logger *log.Logger

func init() {
	logger = log.New(os.Stdout, "", log.LstdFlags)
	logger.SetPrefix(time.Now().Format("2006-01-02 15:04:05") + " - grpc-generator - INFO - ")
}

func GenerateGRPCCode(protoDir, outputDir string) bool {
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		logger.Printf("Failed to create output directory %s: %v", outputDir, err)
		return false
	}

	var protoFiles []string
	err := filepath.Walk(protoDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && strings.HasSuffix(info.Name(), ".proto") {
			protoFiles = append(protoFiles, path)
		}
		return nil
	})

	if err != nil {
		logger.Printf("Failed to walk proto directory %s: %v", protoDir, err)
		return false
	}

	if len(protoFiles) == 0 {
		logger.Printf("No proto files found in %s", protoDir)
		return false
	}

	logger.Printf("Found %d proto files: %v", len(protoFiles), protoFiles)

	initFile := filepath.Join(outputDir, "__init__.py")
	if _, err := os.Stat(initFile); os.IsNotExist(err) {
		file, err := os.Create(initFile)
		if err != nil {
			logger.Printf("Failed to create __init__.py file: %v", err)
			return false
		}
		file.Close()
	}

	script := `
import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("grpc-generator")

def generate_grpc_code(proto_dir, output_dir, proto_files):
    """
    Generate Python gRPC code from proto files.

    Args:
        proto_dir: Directory containing proto files
        output_dir: Directory to output generated code
        proto_files: List of proto files to process
    """
    try:
        import grpc_tools
    except ImportError:
        logger.info("Installing grpcio-tools...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'grpcio-tools'], check=True)

    for proto_file in proto_files:
        logger.info(f"Generating code for {os.path.basename(proto_file)}")

        cmd = [
            'python', '-m', 'grpc_tools.protoc',
            f'--proto_path={proto_dir}',
            f'--python_out={output_dir}',
            f'--grpc_python_out={output_dir}',
            proto_file
        ]

        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Successfully generated code for {os.path.basename(proto_file)}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate code for {os.path.basename(proto_file)}: {e}")
            return False

    return True

# Get arguments from environment variables
proto_dir = os.environ.get('PROTO_DIR')
output_dir = os.environ.get('OUTPUT_DIR')
proto_files_str = os.environ.get('PROTO_FILES')
proto_files = proto_files_str.split(',')

if generate_grpc_code(proto_dir, output_dir, proto_files):
    print("SUCCESS")
else:
    print("FAILURE")
`

	os.Setenv("PROTO_DIR", protoDir)
	os.Setenv("OUTPUT_DIR", outputDir)
	os.Setenv("PROTO_FILES", strings.Join(protoFiles, ","))

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("Failed to execute Python script: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "FAILURE") {
		logger.Printf("Python script failed: %s", outputStr)
		return false
	}

	logger.Printf("Successfully generated gRPC code in %s", outputDir)
	return true
}

func RunGRPCCodeGenerator() int {
	execPath, err := os.Executable()
	if err != nil {
		logger.Printf("Failed to get executable path: %v", err)
		return 1
	}

	baseDir := filepath.Dir(filepath.Dir(execPath))
	if filepath.Base(baseDir) != "agent_runtime" {
		currentDir, err := os.Getwd()
		if err != nil {
			logger.Printf("Failed to get current directory: %v", err)
			return 1
		}

		for {
			if filepath.Base(currentDir) == "agent_runtime" {
				baseDir = currentDir
				break
			}

			parent := filepath.Dir(currentDir)
			if parent == currentDir {
				logger.Printf("Failed to find agent_runtime directory")
				return 1
			}

			currentDir = parent
		}
	}

	protoDir := filepath.Join(baseDir, "protos")
	outputDir := filepath.Join(baseDir, "api", "generated")

	logger.Printf("Base directory: %s", baseDir)
	logger.Printf("Proto directory: %s", protoDir)
	logger.Printf("Output directory: %s", outputDir)

	if !GenerateGRPCCode(protoDir, outputDir) {
		logger.Printf("Failed to generate gRPC code")
		return 1
	}

	return 0
}

func main() {
	os.Exit(RunGRPCCodeGenerator())
}
