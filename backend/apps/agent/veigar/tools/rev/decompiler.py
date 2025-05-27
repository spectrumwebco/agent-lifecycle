"""
Decompilation tools for security review.
"""

import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DecompilerTool:
    """
    Decompiles binary code for security analysis.
    """
    
    def __init__(self):
        """Initialize the decompiler tool."""
        self.decompiled_code = {}
    
    def decompile(self, binary_data: bytes, file_path: str, binary_type: str = "elf", 
                  target_language: str = "c") -> Dict[str, Any]:
        """
        Decompile a binary file to source code.
        
        Args:
            binary_data: The binary data to decompile
            file_path: Path to the binary file
            binary_type: Type of binary (elf, pe, macho)
            target_language: Target language for decompilation (c, cpp, python)
            
        Returns:
            Dict containing the decompiled code and metadata
        """
        if binary_type == "auto":
            binary_type = self._detect_binary_type(binary_data)
        
        logger.info("Decompiling binary file %s of type %s to %s", 
                  file_path, binary_type, target_language)
        
        decompiled_code = self._simulate_decompilation(binary_data, binary_type, target_language)
        
        functions = self._extract_functions(decompiled_code, target_language)
        
        security_functions = self._identify_security_functions(functions, target_language)
        
        return {
            "file_path": file_path,
            "binary_type": binary_type,
            "target_language": target_language,
            "decompiled_code": decompiled_code,
            "functions": functions,
            "security_functions": security_functions
        }
    
    def _detect_binary_type(self, binary_data: bytes) -> str:
        """Detect the type of binary file."""
        if binary_data.startswith(b'\x7fELF'):
            return "elf"
        elif binary_data.startswith(b'MZ'):
            return "pe"
        elif binary_data.startswith(b'\xfe\xed\xfa\xce') or binary_data.startswith(b'\xfe\xed\xfa\xcf') or \
             binary_data.startswith(b'\xca\xfe\xba\xbe') or binary_data.startswith(b'\xce\xfa\xed\xfe'):
            return "macho"
        else:
            return "unknown"
    
    def _simulate_decompilation(self, binary_data: bytes, binary_type: str, 
                               target_language: str) -> str:
        """
        Simulate the decompilation process.
        
        In a real implementation, this would use tools like Ghidra, IDA Pro, or Radare2.
        For this simulation, we'll generate placeholder code based on binary patterns.
        """
        
        strings = self._extract_strings_from_binary(binary_data)
        
        if target_language == "c":
            return self._generate_c_code(binary_type, strings)
        elif target_language == "cpp":
            return self._generate_cpp_code(binary_type, strings)
        elif target_language == "python":
            return self._generate_python_code(binary_type, strings)
        else:
            return f"// Decompilation to {target_language} not supported"
    
    def _extract_strings_from_binary(self, binary_data: bytes) -> List[str]:
        """Extract printable strings from binary data."""
        printable = set(bytes(range(32, 127)))
        result = []
        current_string = b""
        
        for byte in binary_data:
            if byte in printable:
                current_string += bytes([byte])
            elif current_string:
                if len(current_string) >= 4:  # Only keep strings of reasonable length
                    try:
                        result.append(current_string.decode('utf-8', errors='ignore'))
                    except:
                        pass
                current_string = b""
        
        if current_string and len(current_string) >= 4:
            try:
                result.append(current_string.decode('utf-8', errors='ignore'))
            except:
                pass
        
        return result[:20]  # Limit to first 20 strings
    
    def _generate_c_code(self, binary_type: str, strings: List[str]) -> str:
        """Generate simulated C code based on binary type and extracted strings."""
        code = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\n"
        
        for i, string in enumerate(strings[:5]):
            safe_string = string.replace('"', '\\"')
            code += f'const char *g_string_{i} = "{safe_string}";\n'
        
        code += "\n"
        
        code += "int main(int argc, char *argv[]) {\n"
        code += "    printf(\"Program started\\n\");\n\n"
        
        for i, string in enumerate(strings[5:10]):
            if "%" in string:  # Avoid format string issues in the simulation
                string = string.replace("%", "%%")
            safe_string = string.replace('"', '\\"')
            code += f'    printf("{safe_string}\\n");\n'
        
        if binary_type == "elf":
            code += "\n    // Potentially vulnerable code\n"
            code += "    char buffer[64];\n"
            code += "    if (argc > 1) {\n"
            code += "        strcpy(buffer, argv[1]);  // Potential buffer overflow\n"
            code += "        printf(buffer);  // Potential format string vulnerability\n"
            code += "    }\n"
        elif binary_type == "pe":
            code += "\n    // Windows-specific code\n"
            code += "    char buffer[64];\n"
            code += "    if (argc > 1) {\n"
            code += "        strcpy(buffer, argv[1]);  // Potential buffer overflow\n"
            code += "        system(buffer);  // Potential command injection\n"
            code += "    }\n"
        
        code += "\n    return 0;\n"
        code += "}\n"
        
        code += "\n// Additional functions\n"
        code += "void process_data(char *data) {\n"
        code += "    char local_buffer[128];\n"
        code += "    strcpy(local_buffer, data);  // Potential buffer overflow\n"
        code += "    printf(\"Processed: %s\\n\", local_buffer);\n"
        code += "}\n\n"
        
        code += "int authenticate(char *username, char *password) {\n"
        code += "    // Hardcoded credentials for simulation\n"
        code += "    if (strcmp(username, \"admin\") == 0 && strcmp(password, \"password123\") == 0) {\n"
        code += "        return 1;\n"
        code += "    }\n"
        code += "    return 0;\n"
        code += "}\n"
        
        return code
    
    def _generate_cpp_code(self, binary_type: str, strings: List[str]) -> str:
        """Generate simulated C++ code based on binary type and extracted strings."""
        code = "#include <iostream>\n#include <string>\n#include <vector>\n\n"
        
        code += "class DataProcessor {\n"
        code += "private:\n"
        
        for i, string in enumerate(strings[:3]):
            safe_string = string.replace('"', '\\"')
            code += f'    std::string m_string_{i} = "{safe_string}";\n'
        
        code += "\npublic:\n"
        code += "    DataProcessor() {}\n\n"
        
        code += "    void processData(const std::string& data) {\n"
        code += "        char buffer[64];\n"
        code += "        // Potentially unsafe operation for demonstration\n"
        code += "        strcpy(buffer, data.c_str());  // Potential buffer overflow\n"
        code += "        std::cout << \"Processed: \" << buffer << std::endl;\n"
        code += "    }\n\n"
        
        code += "    bool authenticate(const std::string& username, const std::string& password) {\n"
        code += "        // Hardcoded credentials for simulation\n"
        code += "        if (username == \"admin\" && password == \"password123\") {\n"
        code += "            return true;\n"
        code += "        }\n"
        code += "        return false;\n"
        code += "    }\n"
        
        code += "};\n\n"
        
        code += "int main(int argc, char *argv[]) {\n"
        code += "    std::cout << \"Program started\" << std::endl;\n\n"
        
        code += "    DataProcessor processor;\n\n"
        
        for i, string in enumerate(strings[5:8]):
            safe_string = string.replace('"', '\\"')
            code += f'    std::cout << "{safe_string}" << std::endl;\n'
        
        if binary_type == "elf" or binary_type == "pe":
            code += "\n    // Potentially vulnerable code\n"
            code += "    if (argc > 1) {\n"
            code += "        processor.processData(argv[1]);\n"
            code += "    }\n"
        
        code += "\n    return 0;\n"
        code += "}\n"
        
        return code
    
    def _generate_python_code(self, binary_type: str, strings: List[str]) -> str:
        """Generate simulated Python code based on binary type and extracted strings."""
        code = "#!/usr/bin/env python3\n"
        code += "import os\n"
        code += "import sys\n"
        code += "import subprocess\n\n"
        
        for i, string in enumerate(strings[:5]):
            safe_string = string.replace('"', '\\"').replace("'", "\\'")
            code += f'G_STRING_{i} = "{safe_string}"\n'
        
        code += "\n"
        
        code += "class DataProcessor:\n"
        code += "    def __init__(self):\n"
        
        for i, string in enumerate(strings[5:8]):
            safe_string = string.replace('"', '\\"').replace("'", "\\'")
            code += f'        self.string_{i} = "{safe_string}"\n'
        
        code += "\n"
        
        code += "    def process_data(self, data):\n"
        code += "        print(f\"Processing: {data}\")\n"
        code += "        # Potentially unsafe operation for demonstration\n"
        code += "        os.system(f\"echo {data}\")  # Potential command injection\n"
        code += "        return data\n\n"
        
        code += "    def authenticate(self, username, password):\n"
        code += "        # Hardcoded credentials for simulation\n"
        code += "        if username == \"admin\" and password == \"password123\":\n"
        code += "            return True\n"
        code += "        return False\n\n"
        
        code += "def main():\n"
        code += "    print(\"Program started\")\n\n"
        
        code += "    processor = DataProcessor()\n\n"
        
        for i, string in enumerate(strings[8:11]):
            safe_string = string.replace('"', '\\"').replace("'", "\\'")
            code += f'    print("{safe_string}")\n'
        
        code += "\n    # Potentially vulnerable code\n"
        code += "    if len(sys.argv) > 1:\n"
        code += "        processor.process_data(sys.argv[1])\n"
        code += "        # Potential eval injection\n"
        code += "        eval(f\"print('Processing argument: {sys.argv[1]}')\")\n"
        
        code += "\n"
        code += "if __name__ == \"__main__\":\n"
        code += "    main()\n"
        
        return code
    
    def _extract_functions(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Extract function definitions from decompiled code."""
        functions = []
        
        if language == "c" or language == "cpp":
            pattern = r'(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{'
            matches = re.finditer(pattern, code)
            
            for match in matches:
                return_type = match.group(1)
                name = match.group(2)
                params = match.group(3)
                
                functions.append({
                    "name": name,
                    "return_type": return_type,
                    "parameters": params.strip(),
                    "start_pos": match.start(),
                    "language": language
                })
        
        elif language == "python":
            pattern = r'def\s+(\w+)\s*\(([^)]*)\):'
            matches = re.finditer(pattern, code)
            
            for match in matches:
                name = match.group(1)
                params = match.group(2)
                
                functions.append({
                    "name": name,
                    "parameters": params.strip(),
                    "start_pos": match.start(),
                    "language": language
                })
        
        return functions
    
    def _identify_security_functions(self, functions: List[Dict[str, Any]], 
                                    language: str) -> List[Dict[str, Any]]:
        """Identify security-relevant functions from the extracted functions."""
        security_functions = []
        
        security_keywords = [
            "auth", "password", "crypt", "hash", "encrypt", "decrypt", 
            "secure", "token", "key", "cert", "validate", "verify"
        ]
        
        for function in functions:
            name = function["name"].lower()
            
            if any(keyword in name for keyword in security_keywords):
                security_functions.append(function)
                continue
            
            params = function.get("parameters", "").lower()
            if any(keyword in params for keyword in security_keywords):
                security_functions.append(function)
        
        return security_functions
