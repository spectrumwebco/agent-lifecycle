package utils

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var logger = log.New(os.Stdout, "[Workspace] ", log.LstdFlags)

func CreateWorkspace() string {
	workspaceID := uuid.New().String()
	
	settings, err := core.GetSettings()
	if err != nil {
		logger.Printf("Error getting settings: %v", err)
		return ""
	}
	
	workspacesDir, ok := settings.Get("WORKSPACES_DIR")
	if !ok {
		logger.Printf("WORKSPACES_DIR not found in settings")
		return ""
	}
	
	workspacePath := filepath.Join(workspacesDir.(string), workspaceID)
	err = os.MkdirAll(workspacePath, 0755)
	if err != nil {
		logger.Printf("Error creating workspace directory: %v", err)
		return ""
	}
	
	logger.Printf("Created workspace at %s", workspacePath)
	
	return workspaceID
}

func GetWorkspacePath(workspaceID string) string {
	settings, err := core.GetSettings()
	if err != nil {
		logger.Printf("Error getting settings: %v", err)
		return ""
	}
	
	workspacesDir, ok := settings.Get("WORKSPACES_DIR")
	if !ok {
		logger.Printf("WORKSPACES_DIR not found in settings")
		return ""
	}
	
	return filepath.Join(workspacesDir.(string), workspaceID)
}

type FileInfo struct {
	Path         string  `json:"path"`
	Name         string  `json:"name"`
	Size         int64   `json:"size"`
	LastModified float64 `json:"last_modified"`
	IsDirectory  bool    `json:"is_directory"`
}

func ListWorkspaceFiles(workspacePath string) []FileInfo {
	files := []FileInfo{}
	
	err := filepath.Walk(workspacePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		if filepath.Base(path)[0] == '.' {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		
		relPath, err := filepath.Rel(workspacePath, path)
		if err != nil {
			return err
		}
		
		if relPath == "." {
			return nil
		}
		
		fileInfo := FileInfo{
			Path:         relPath,
			Name:         info.Name(),
			Size:         info.Size(),
			LastModified: float64(info.ModTime().Unix()),
			IsDirectory:  info.IsDir(),
		}
		
		files = append(files, fileInfo)
		
		return nil
	})
	
	if err != nil {
		logger.Printf("Error listing workspace files: %v", err)
	}
	
	return files
}

func ReadFileContent(filePath string) string {
	content, err := ioutil.ReadFile(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			logger.Printf("File not found: %s", filePath)
			return fmt.Sprintf("Error reading file: %v", err)
		}
		
		logger.Printf("Error reading file %s: %v", filePath, err)
		return fmt.Sprintf("Error reading file: %v", err)
	}
	
	return string(content)
}

func WriteFileContent(filePath string, content string) bool {
	err := os.MkdirAll(filepath.Dir(filePath), 0755)
	if err != nil {
		logger.Printf("Error creating directory for file %s: %v", filePath, err)
		return false
	}
	
	err = ioutil.WriteFile(filePath, []byte(content), 0644)
	if err != nil {
		logger.Printf("Error writing to file %s: %v", filePath, err)
		return false
	}
	
	return true
}

func DeleteFile(filePath string) bool {
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			logger.Printf("File not found: %s", filePath)
			return false
		}
		
		logger.Printf("Error getting file info for %s: %v", filePath, err)
		return false
	}
	
	if fileInfo.IsDir() {
		err = os.RemoveAll(filePath)
	} else {
		err = os.Remove(filePath)
	}
	
	if err != nil {
		logger.Printf("Error deleting file %s: %v", filePath, err)
		return false
	}
	
	return true
}

func CreateDirectory(dirPath string) bool {
	err := os.MkdirAll(dirPath, 0755)
	if err != nil {
		logger.Printf("Error creating directory %s: %v", dirPath, err)
		return false
	}
	
	return true
}

func CopyFile(srcPath string, dstPath string) bool {
	srcInfo, err := os.Stat(srcPath)
	if err != nil {
		logger.Printf("Error getting source file info: %v", err)
		return false
	}
	
	err = os.MkdirAll(filepath.Dir(dstPath), 0755)
	if err != nil {
		logger.Printf("Error creating destination directory: %v", err)
		return false
	}
	
	if srcInfo.IsDir() {
		err = filepath.Walk(srcPath, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			
			relPath, err := filepath.Rel(srcPath, path)
			if err != nil {
				return err
			}
			
			dstItemPath := filepath.Join(dstPath, relPath)
			
			if info.IsDir() {
				return os.MkdirAll(dstItemPath, info.Mode())
			}
			
			return copyFileContents(path, dstItemPath)
		})
	} else {
		err = copyFileContents(srcPath, dstPath)
	}
	
	if err != nil {
		logger.Printf("Error copying file %s to %s: %v", srcPath, dstPath, err)
		return false
	}
	
	return true
}

func copyFileContents(src, dst string) error {
	srcFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer srcFile.Close()
	
	dstFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer dstFile.Close()
	
	_, err = dstFile.ReadFrom(srcFile)
	return err
}

func MoveFile(srcPath string, dstPath string) bool {
	err := os.MkdirAll(filepath.Dir(dstPath), 0755)
	if err != nil {
		logger.Printf("Error creating destination directory: %v", err)
		return false
	}
	
	err = os.Rename(srcPath, dstPath)
	if err != nil {
		if CopyFile(srcPath, dstPath) {
			return DeleteFile(srcPath)
		}
		
		logger.Printf("Error moving file %s to %s: %v", srcPath, dstPath, err)
		return false
	}
	
	return true
}

func RenameFile(filePath string, newName string) bool {
	dirPath := filepath.Dir(filePath)
	newPath := filepath.Join(dirPath, newName)
	
	err := os.Rename(filePath, newPath)
	if err != nil {
		logger.Printf("Error renaming file %s to %s: %v", filePath, newName, err)
		return false
	}
	
	return true
}

func GetFileInfo(filePath string) *FileInfo {
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		
		logger.Printf("Error getting file info for %s: %v", filePath, err)
		return nil
	}
	
	info := &FileInfo{
		Path:         filePath,
		Name:         filepath.Base(filePath),
		LastModified: float64(fileInfo.ModTime().Unix()),
		IsDirectory:  fileInfo.IsDir(),
	}
	
	if !fileInfo.IsDir() {
		info.Size = fileInfo.Size()
	}
	
	return info
}

func init() {
	core.RegisterFunction("create_workspace", CreateWorkspace)
	core.RegisterFunction("get_workspace_path", GetWorkspacePath)
	core.RegisterFunction("list_workspace_files", ListWorkspaceFiles)
	core.RegisterFunction("read_file_content", ReadFileContent)
	core.RegisterFunction("write_file_content", WriteFileContent)
	core.RegisterFunction("delete_file", DeleteFile)
	core.RegisterFunction("create_directory", CreateDirectory)
	core.RegisterFunction("copy_file", CopyFile)
	core.RegisterFunction("move_file", MoveFile)
	core.RegisterFunction("rename_file", RenameFile)
	core.RegisterFunction("get_file_info", GetFileInfo)
}
