"""
Simple script to verify the directory structure for Kled and Veigar agents.
"""

import os
from pathlib import Path

def check_directory_exists(path, name):
    """Check if a directory exists and print the result."""
    exists = os.path.isdir(path)
    print(f"{name} directory {'exists' if exists else 'does not exist'} at {path}")
    return exists

def main():
    """Main function to verify the directory structure."""
    base_dir = Path("/home/ubuntu/repos/agent_runtime/backend/apps/python_agent")
    
    print("\n=== Checking Kled Directory Structure ===")
    kled_base = base_dir / "kled"
    kled_exists = check_directory_exists(kled_base, "Kled base")
    
    if kled_exists:
        check_directory_exists(kled_base / "agent", "Kled agent")
        check_directory_exists(kled_base / "tools", "Kled tools")
        check_directory_exists(kled_base / "config", "Kled config")
        check_directory_exists(kled_base / "django_integration", "Kled django_integration")
        check_directory_exists(kled_base / "django_models", "Kled django_models")
        check_directory_exists(kled_base / "django_views", "Kled django_views")
        check_directory_exists(kled_base / "go_integration", "Kled go_integration")
    
    print("\n=== Checking Veigar Directory Structure ===")
    veigar_base = base_dir / "veigar"
    veigar_exists = check_directory_exists(veigar_base, "Veigar base")
    
    if veigar_exists:
        check_directory_exists(veigar_base / "agent", "Veigar agent")
        check_directory_exists(veigar_base / "tools", "Veigar tools")
        check_directory_exists(veigar_base / "config", "Veigar config")
        check_directory_exists(veigar_base / "django_integration", "Veigar django_integration")
        check_directory_exists(veigar_base / "django_models", "Veigar django_models")
        check_directory_exists(veigar_base / "tools" / "crypto", "Veigar crypto tools")
        check_directory_exists(veigar_base / "tools" / "pwn", "Veigar pwn tools")
        check_directory_exists(veigar_base / "tools" / "rev", "Veigar rev tools")
        check_directory_exists(veigar_base / "tools" / "web", "Veigar web tools")
        check_directory_exists(veigar_base / "tools" / "forensics", "Veigar forensics tools")
        check_directory_exists(veigar_base / "tools" / "common", "Veigar common tools")
    
    print("\n=== Checking Agent Framework Directory Structure ===")
    framework_base = base_dir / "agent_framework"
    framework_exists = check_directory_exists(framework_base, "Agent Framework base")
    
    if framework_exists:
        check_directory_exists(framework_base / "shared", "Agent Framework shared")
        check_directory_exists(framework_base / "trajectory", "Agent Framework trajectory")
    
    print("\nVerification complete!")

if __name__ == "__main__":
    main()
