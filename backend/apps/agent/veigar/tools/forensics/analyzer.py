"""
Digital forensics analysis tools.
"""

import logging
import math
import os
import re
import subprocess
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ForensicsAnalyzer:
    """
    Analyzes files and data for digital forensics investigations.
    """
    
    def __init__(self):
        """Initialize the forensics analyzer."""
        self.findings = []
        
    def analyze_network_traffic(self, pcap_file: str) -> Dict[str, Any]:
        """
        Analyze network traffic from a PCAP file.
        
        Args:
            pcap_file: Path to the PCAP file
            
        Returns:
            Dictionary containing analysis results
        """
        self.findings = []
        
        if not os.path.exists(pcap_file):
            return {
                "status": "error",
                "error": f"File not found: {pcap_file}",
                "findings": []
            }
        
        try:
            self._analyze_network_capture(pcap_file)
            
            return {
                "status": "success",
                "file": pcap_file,
                "findings": self.findings
            }
        except Exception as e:
            logger.error("Error analyzing network traffic: %s", str(e))
            return {
                "status": "error",
                "error": str(e),
                "findings": self.findings
            }
    
    def analyze_memory_dump(self, memory_file: str) -> Dict[str, Any]:
        """
        Analyze a memory dump file.
        
        Args:
            memory_file: Path to the memory dump file
            
        Returns:
            Dictionary containing analysis results
        """
        self.findings = []
        
        if not os.path.exists(memory_file):
            return {
                "status": "error",
                "error": f"File not found: {memory_file}",
                "findings": []
            }
        
        try:
            self._analyze_memory_dump(memory_file)
            
            return {
                "status": "success",
                "file": memory_file,
                "findings": self.findings
            }
        except Exception as e:
            logger.error("Error analyzing memory dump: %s", str(e))
            return {
                "status": "error",
                "error": str(e),
                "findings": self.findings
            }
    
    def analyze_disk_image(self, disk_file: str) -> Dict[str, Any]:
        """
        Analyze a disk image file.
        
        Args:
            disk_file: Path to the disk image file
            
        Returns:
            Dictionary containing analysis results
        """
        self.findings = []
        
        if not os.path.exists(disk_file):
            return {
                "status": "error",
                "error": f"File not found: {disk_file}",
                "findings": []
            }
        
        try:
            self._analyze_disk_image(disk_file)
            
            return {
                "status": "success",
                "file": disk_file,
                "findings": self.findings
            }
        except Exception as e:
            logger.error("Error analyzing disk image: %s", str(e))
            return {
                "status": "error",
                "error": str(e),
                "findings": self.findings
            }
    
    def analyze_image_metadata(self, image_file: str) -> Dict[str, Any]:
        """
        Analyze metadata from an image file.
        
        Args:
            image_file: Path to the image file
            
        Returns:
            Dictionary containing metadata analysis results
        """
        if not os.path.exists(image_file):
            return {
                "status": "error",
                "error": f"File not found: {image_file}",
                "metadata": {}
            }
        
        try:
            try:
                exif_output = subprocess.run(
                    ["exiftool", image_file],
                    capture_output=True, text=True, timeout=30
                )
                
                if exif_output.returncode == 0:
                    metadata = {}
                    for line in exif_output.stdout.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
                    
                    # Check for GPS coordinates
                    has_gps = False
                    if "GPS Latitude" in metadata or "GPS Longitude" in metadata:
                        has_gps = True
                    
                    # Check for author/creator information
                    has_author = False
                    for key in ["Author", "Creator", "Owner", "Copyright"]:
                        if any(k.lower() == key.lower() for k in metadata.keys()):
                            has_author = True
                            break
                    
                    return {
                        "status": "success",
                        "file": image_file,
                        "metadata": metadata,
                        "analysis": {
                            "has_gps_data": has_gps,
                            "has_author_info": has_author,
                            "metadata_count": len(metadata)
                        }
                    }
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("exiftool not available, using fallback method for metadata analysis")
                
                image_type = os.path.splitext(image_file)[1].lower()
                creation_time = os.path.getctime(image_file)
                modification_time = os.path.getmtime(image_file)
                size = os.path.getsize(image_file)
                
                metadata = {
                    "File Name": os.path.basename(image_file),
                    "File Size": f"{size} bytes",
                    "File Type": image_type.replace(".", "").upper(),
                    "Creation Time": str(creation_time),
                    "Modification Time": str(modification_time)
                }
                
                return {
                    "status": "success",
                    "file": image_file,
                    "metadata": metadata,
                    "analysis": {
                        "has_gps_data": False,
                        "has_author_info": False,
                        "metadata_count": len(metadata),
                        "note": "Limited metadata available (exiftool not installed)"
                    }
                }
            
            return {
                "status": "error",
                "error": "Unknown error during metadata analysis",
                "metadata": {}
            }
        except Exception as e:
            logger.error("Error analyzing image metadata: %s", str(e))
            return {
                "status": "error",
                "error": str(e),
                "metadata": {}
            }
    
    def analyze_image_steganography(self, image_file: str, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze an image file for hidden data using steganography techniques.
        
        Args:
            image_file: Path to the image file
            password: Optional password to extract hidden data
            
        Returns:
            Dictionary containing steganography analysis results
        """
        if not os.path.exists(image_file):
            return {
                "status": "error",
                "error": f"File not found: {image_file}",
                "findings": []
            }
        
        try:
            try:
                cmd = ["steghide", "info", image_file]
                if password:
                    cmd.extend(["-p", password])
                
                info_output = subprocess.run(
                    cmd,
                    capture_output=True, text=True, timeout=30
                )
                
                if "contains embedded data" in info_output.stdout:
                    extract_cmd = ["steghide", "extract", "-sf", image_file]
                    if password:
                        extract_cmd.extend(["-p", password])
                    else:
                        extract_cmd.extend(["-p", ""])  # Empty password
                    
                    extract_output = subprocess.run(
                        extract_cmd,
                        capture_output=True, text=True, timeout=30
                    )
                    
                    if extract_output.returncode == 0:
                        extracted_file = re.search(r'wrote extracted data to "([^"]+)"', extract_output.stdout)
                        if extracted_file:
                            filename = extracted_file.group(1)
                            with open(filename, 'r') as f:
                                hidden_data = f.read()
                            
                            return {
                                "status": "success",
                                "file": image_file,
                                "has_hidden_data": True,
                                "hidden_data": hidden_data,
                                "extraction_method": "steghide"
                            }
                    
                    return {
                        "status": "success",
                        "file": image_file,
                        "has_hidden_data": True,
                        "hidden_data": None,
                        "note": "Hidden data detected but could not be extracted (incorrect password?)",
                        "extraction_method": "steghide"
                    }
                else:
                    return {
                        "status": "success",
                        "file": image_file,
                        "has_hidden_data": False,
                        "analysis_method": "steghide"
                    }
                    
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("steghide not available, using fallback method for steganography analysis")
                
                with open(image_file, 'rb') as f:
                    data = f.read()
                
                # Check for suspicious patterns in binary data
                suspicious_patterns = [
                    b'PK\x03\x04',  # ZIP signature
                    b'%PDF',        # PDF signature
                    b'\xFF\xD8\xFF\xE0',  # JPEG signature (inside another JPEG)
                    b'<!DOCTYPE',   # HTML signature
                    b'<html',       # HTML signature
                    b'<?xml'        # XML signature
                ]
                
                found_patterns = []
                for pattern in suspicious_patterns:
                    if pattern in data[100:]:  # Skip header
                        found_patterns.append(pattern)
                
                entropy = 0
                if data:
                    byte_counts = {}
                    for byte in data:
                        if byte in byte_counts:
                            byte_counts[byte] += 1
                        else:
                            byte_counts[byte] = 1
                    
                    file_size = len(data)
                    entropy = 0
                    for count in byte_counts.values():
                        probability = count / file_size
                        entropy -= probability * math.log2(probability)
                
                has_hidden_data = len(found_patterns) > 0 or entropy > 7.5
                
                return {
                    "status": "success",
                    "file": image_file,
                    "has_hidden_data": has_hidden_data,
                    "analysis": {
                        "entropy": entropy,
                        "suspicious_patterns": [str(p) for p in found_patterns],
                        "file_size": len(data)
                    },
                    "note": "Limited analysis (steghide not installed)",
                    "analysis_method": "basic entropy and pattern analysis"
                }
                
        except Exception as e:
            logger.error("Error analyzing image steganography: %s", str(e))
            return {
                "status": "error",
                "error": str(e),
                "has_hidden_data": False
            }
    
    def comprehensive_analysis(self, network_file: Optional[str] = None, 
                              memory_file: Optional[str] = None,
                              disk_file: Optional[str] = None,
                              image_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a comprehensive forensic analysis on multiple artifacts.
        
        Args:
            network_file: Optional path to network capture file
            memory_file: Optional path to memory dump file
            disk_file: Optional path to disk image file
            image_file: Optional path to image file
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        results = {
            "status": "success",
            "analyses": {},
            "summary": {
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }
        }
        
        if network_file:
            network_analysis = self.analyze_network_traffic(network_file)
            results["analyses"]["network"] = network_analysis
            if network_analysis["status"] == "success":
                self._update_summary(results["summary"], network_analysis.get("findings", []))
        
        if memory_file:
            memory_analysis = self.analyze_memory_dump(memory_file)
            results["analyses"]["memory"] = memory_analysis
            if memory_analysis["status"] == "success":
                self._update_summary(results["summary"], memory_analysis.get("findings", []))
        
        if disk_file:
            disk_analysis = self.analyze_disk_image(disk_file)
            results["analyses"]["disk"] = disk_analysis
            if disk_analysis["status"] == "success":
                self._update_summary(results["summary"], disk_analysis.get("findings", []))
        
        if image_file:
            image_metadata = self.analyze_image_metadata(image_file)
            image_stego = self.analyze_image_steganography(image_file)
            
            results["analyses"]["image"] = {
                "metadata": image_metadata,
                "steganography": image_stego
            }
            
            if image_stego["status"] == "success" and image_stego.get("has_hidden_data", False):
                results["summary"]["total_findings"] += 1
                results["summary"]["high"] += 1
        
        return results
    
    def _update_summary(self, summary: Dict[str, int], findings: List[Dict[str, Any]]) -> None:
        """Update the summary with findings."""
        summary["total_findings"] += len(findings)
        
        for finding in findings:
            severity = finding.get("severity", "info").lower()
            if severity in ["critical", "high", "medium", "low", "info"]:
                summary[severity] += 1
    
    def analyze_file(self, file_path: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analyze a file for forensic evidence.
        
        Args:
            file_path: Path to the file to analyze
            analysis_type: Type of analysis to perform (general, network, memory, disk)
            
        Returns:
            Dict containing the analysis results
        """
        self.findings = []
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "findings": []
            }
        
        try:
            file_type = self._determine_file_type(file_path)
            
            if analysis_type == "network" or file_type == "pcap":
                self._analyze_network_capture(file_path)
            elif analysis_type == "memory" or file_type == "memory_dump":
                self._analyze_memory_dump(file_path)
            elif analysis_type == "disk" or file_type == "disk_image":
                self._analyze_disk_image(file_path)
            elif file_type == "image":
                self._analyze_image(file_path)
            else:
                self._analyze_general_file(file_path)
            
            return {
                "success": True,
                "file_type": file_type,
                "findings": self.findings
            }
            
        except Exception as e:
            logger.error("Error analyzing file %s: %s", file_path, str(e))
            return {
                "success": False,
                "error": str(e),
                "findings": self.findings
            }
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine the type of file."""
        try:
            result = subprocess.run(["file", file_path], capture_output=True, text=True, check=True)
            file_output = result.stdout.lower()
            
            if "pcap" in file_output or "capture file" in file_output:
                return "pcap"
            elif "memory dump" in file_output or "memory image" in file_output:
                return "memory_dump"
            elif "disk image" in file_output or "filesystem" in file_output:
                return "disk_image"
            elif any(ext in file_output for ext in ["jpeg", "jpg", "png", "gif", "bmp"]):
                return "image"
            elif "text" in file_output:
                return "text"
            elif "executable" in file_output:
                return "executable"
            elif "zip" in file_output or "archive" in file_output:
                return "archive"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error("Error determining file type: %s", str(e))
            return "unknown"
    
    def _analyze_network_capture(self, file_path: str) -> None:
        """Analyze a network capture file (PCAP)."""
        try:
            self.findings.append({
                "type": "info",
                "description": "Network capture file detected",
                "details": "Analyzing PCAP file for protocols, IPs, and suspicious traffic"
            })
            
            try:
                protocol_stats = subprocess.run(
                    ["tshark", "-r", file_path, "-q", "-z", "io,phs"],
                    capture_output=True, text=True, timeout=30
                )
                
                if protocol_stats.returncode == 0:
                    protocols = {}
                    for line in protocol_stats.stdout.split('\n'):
                        if ':' in line and not line.startswith('==='):
                            parts = line.split(':')
                            if len(parts) >= 2:
                                protocol = parts[0].strip()
                                if protocol and protocol != "Protocol Hierarchy Statistics":
                                    protocols[protocol] = True
                    
                    self.findings.append({
                        "type": "protocol_analysis",
                        "description": "Protocol analysis",
                        "details": {
                            "protocols_detected": list(protocols.keys())
                        }
                    })
            except subprocess.SubprocessError:
                logger.warning("tshark not available, using fallback method for protocol analysis")
                
                strings_output = subprocess.run(
                    ["strings", file_path], 
                    capture_output=True, text=True
                )
                
                protocols = {
                    "http": len(re.findall(r'HTTP/[0-9.]+', strings_output.stdout)) > 0,
                    "dns": len(re.findall(r'DNS', strings_output.stdout)) > 0,
                    "smtp": len(re.findall(r'SMTP|MAIL FROM|RCPT TO', strings_output.stdout)) > 0,
                    "ftp": len(re.findall(r'FTP|USER|PASS|RETR|STOR', strings_output.stdout)) > 0,
                    "ssh": len(re.findall(r'SSH', strings_output.stdout)) > 0,
                    "tls": len(re.findall(r'TLS|SSL', strings_output.stdout)) > 0
                }
                
                detected_protocols = [p for p, detected in protocols.items() if detected]
                
                self.findings.append({
                    "type": "protocol_analysis",
                    "description": "Protocol analysis (fallback method)",
                    "details": {
                        "protocols_detected": detected_protocols
                    }
                })
            
            ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            
            try:
                ip_extraction = subprocess.run(
                    ["tshark", "-r", file_path, "-T", "fields", "-e", "ip.src", "-e", "ip.dst"],
                    capture_output=True, text=True, timeout=30
                )
                
                if ip_extraction.returncode == 0:
                    all_ips = re.findall(ip_pattern, ip_extraction.stdout)
                    unique_ips = list(set(all_ips))
                    
                    ip_counts = {}
                    for ip in all_ips:
                        if ip in ip_counts:
                            ip_counts[ip] += 1
                        else:
                            ip_counts[ip] = 1
                    
                    sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)
                    top_ips = sorted_ips[:10]  # Top 10 most frequent IPs
                    
                    self.findings.append({
                        "type": "ip_analysis",
                        "description": "IP address analysis",
                        "details": {
                            "unique_ip_count": len(unique_ips),
                            "top_ips": [{"ip": ip, "count": count} for ip, count in top_ips]
                        }
                    })
            except subprocess.SubprocessError:
                logger.warning("tshark not available, using fallback method for IP analysis")
                strings_output = subprocess.run(
                    ["strings", file_path], 
                    capture_output=True, text=True
                )
                
                all_ips = re.findall(ip_pattern, strings_output.stdout)
                unique_ips = list(set(all_ips))
                
                self.findings.append({
                    "type": "ip_analysis",
                    "description": "IP address analysis (fallback method)",
                    "details": {
                        "unique_ip_count": len(unique_ips),
                        "ips_found": unique_ips[:20]  # Limit to first 20 IPs
                    }
                })
            
            suspicious_patterns = {
                "unusual_ports": False,
                "data_exfiltration": False,
                "c2_traffic": False,
                "suspicious_domains": []
            }
            
            try:
                port_extraction = subprocess.run(
                    ["tshark", "-r", file_path, "-T", "fields", "-e", "tcp.dstport", "-e", "udp.dstport"],
                    capture_output=True, text=True, timeout=30
                )
                
                if port_extraction.returncode == 0:
                    ports = [int(p) for p in port_extraction.stdout.split() if p.isdigit()]
                    unusual_ports = [p for p in ports if p > 1024 and p not in [8080, 8443, 3000, 3001, 5000, 5001]]
                    
                    if unusual_ports:
                        suspicious_patterns["unusual_ports"] = True
                        suspicious_patterns["unusual_port_list"] = list(set(unusual_ports))[:10]
                
                dns_extraction = subprocess.run(
                    ["tshark", "-r", file_path, "-Y", "dns", "-T", "fields", "-e", "dns.qry.name"],
                    capture_output=True, text=True, timeout=30
                )
                
                if dns_extraction.returncode == 0:
                    domains = dns_extraction.stdout.split()
                    suspicious_domain_patterns = [
                        r'[a-zA-Z0-9]{10,}\.[a-z]{2,3}$',  # Long random-looking domains
                        r'[0-9a-f]{8,}\.[a-z]{2,3}$',      # Hex-looking domains
                        r'\.ru$|\.cn$|\.su$'               # Certain TLDs often used in attacks
                    ]
                    
                    for domain in domains:
                        for pattern in suspicious_domain_patterns:
                            if re.search(pattern, domain):
                                suspicious_patterns["suspicious_domains"].append(domain)
                                break
                
                if "http" in protocols or "ftp" in protocols:
                    suspicious_patterns["data_exfiltration"] = True
                
                if suspicious_patterns["unusual_ports"] or suspicious_patterns["suspicious_domains"]:
                    suspicious_patterns["c2_traffic"] = True
                
                self.findings.append({
                    "type": "traffic_analysis",
                    "description": "Traffic pattern analysis",
                    "details": suspicious_patterns
                })
                
            except subprocess.SubprocessError:
                logger.warning("tshark not available, skipping detailed traffic analysis")
                self.findings.append({
                    "type": "traffic_analysis",
                    "description": "Traffic pattern analysis",
                    "details": "Detailed traffic analysis requires tshark (Wireshark CLI)"
                })
            
        except Exception as e:
            logger.error("Error analyzing network capture: %s", str(e))
            self.findings.append({
                "type": "error",
                "description": f"Error analyzing network capture: {str(e)}"
            })
    
    def _analyze_memory_dump(self, file_path: str) -> None: 
        """Analyze a memory dump file."""
        try:
            self.findings.append({
                "type": "info",
                "description": "Memory dump file detected",
                "details": "Analyzing memory dump for processes, network connections, and artifacts"
            })
            
            try:
                process_list = subprocess.run(
                    ["volatility", "-f", file_path, "pslist"],
                    capture_output=True, text=True, timeout=60
                )
                
                if process_list.returncode == 0:
                    processes = []
                    for line in process_list.stdout.split('\n'):
                        if line and not line.startswith('Volatility') and not line.startswith('Offset'):
                            parts = line.split()
                            if len(parts) >= 6:
                                processes.append({
                                    "pid": parts[2],
                                    "name": parts[1],
                                    "start_time": parts[4] + " " + parts[5]
                                })
                    
                    self.findings.append({
                        "type": "process_analysis",
                        "description": "Process analysis",
                        "details": {
                            "process_count": len(processes),
                            "processes": processes[:20]  # Limit to first 20 processes
                        }
                    })
                    
                    hidden_processes = subprocess.run(
                        ["volatility", "-f", file_path, "psxview"],
                        capture_output=True, text=True, timeout=60
                    )
                    
                    if hidden_processes.returncode == 0:
                        hidden = []
                        for line in hidden_processes.stdout.split('\n'):
                            if "False" in line:
                                parts = line.split()
                                if len(parts) >= 3:
                                    hidden.append({
                                        "pid": parts[2],
                                        "name": parts[1]
                                    })
                        
                        if hidden:
                            self.findings.append({
                                "type": "hidden_processes",
                                "description": "Hidden processes detected",
                                "details": {
                                    "count": len(hidden),
                                    "processes": hidden
                                }
                            })
                
                network_connections = subprocess.run(
                    ["volatility", "-f", file_path, "netscan"],
                    capture_output=True, text=True, timeout=60
                )
                
                if network_connections.returncode == 0:
                    connections = []
                    listening_ports = []
                    
                    for line in network_connections.stdout.split('\n'):
                        if "ESTABLISHED" in line or "LISTENING" in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                conn = {
                                    "protocol": parts[1],
                                    "local_address": parts[2],
                                    "remote_address": parts[3],
                                    "state": parts[4]
                                }
                                
                                if "LISTENING" in line:
                                    listening_ports.append(conn)
                                else:
                                    connections.append(conn)
                    
                    self.findings.append({
                        "type": "network_connections",
                        "description": "Network connection analysis",
                        "details": {
                            "active_connections": connections[:10],  # Limit to first 10 connections
                            "listening_ports": listening_ports[:10]  # Limit to first 10 listening ports
                        }
                    })
                
                registry_hives = subprocess.run(
                    ["volatility", "-f", file_path, "hivelist"],
                    capture_output=True, text=True, timeout=60
                )
                
                if registry_hives.returncode == 0:
                    hives = []
                    for line in registry_hives.stdout.split('\n'):
                        if "\\Registry\\" in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                hives.append(parts[-1])
                    
                    self.findings.append({
                        "type": "registry_analysis",
                        "description": "Registry analysis",
                        "details": {
                            "hive_count": len(hives),
                            "hives": hives
                        }
                    })
                
                cmdscan = subprocess.run(
                    ["volatility", "-f", file_path, "cmdscan"],
                    capture_output=True, text=True, timeout=60
                )
                
                if cmdscan.returncode == 0:
                    commands = []
                    for line in cmdscan.stdout.split('\n'):
                        if "Command" in line:
                            parts = line.split(":", 1)
                            if len(parts) >= 2:
                                commands.append(parts[1].strip())
                    
                    if commands:
                        self.findings.append({
                            "type": "command_history",
                            "description": "Command history analysis",
                            "details": {
                                "command_count": len(commands),
                                "commands": commands
                            }
                        })
                
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("Volatility not available, using fallback method for memory analysis")
                
                strings_output = subprocess.run(
                    ["strings", file_path], 
                    capture_output=True, text=True
                )
                
                process_patterns = [
                    r'(cmd\.exe|powershell\.exe|bash|sh|explorer\.exe|svchost\.exe|lsass\.exe|csrss\.exe)',
                    r'(chrome|firefox|iexplore|edge|safari)\.exe',
                    r'(notepad|word|excel|powerpoint|outlook)\.exe'
                ]
                
                processes = set()
                for pattern in process_patterns:
                    matches = re.findall(pattern, strings_output.stdout, re.IGNORECASE)
                    processes.update(matches)
                
                self.findings.append({
                    "type": "process_analysis",
                    "description": "Process analysis (fallback method)",
                    "details": {
                        "process_count": len(processes),
                        "processes": list(processes)
                    }
                })
                
                ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
                url_pattern = r'https?://[^\s]+'
                
                ips = set(re.findall(ip_pattern, strings_output.stdout))
                urls = set(re.findall(url_pattern, strings_output.stdout))
                
                self.findings.append({
                    "type": "network_artifacts",
                    "description": "Network artifacts (fallback method)",
                    "details": {
                        "ip_addresses": list(ips)[:20],
                        "urls": list(urls)[:20]
                    }
                })
                
                registry_pattern = r'HKEY_[A-Z_]+\\[^\s]+'
                registry_keys = set(re.findall(registry_pattern, strings_output.stdout))
                
                if registry_keys:
                    self.findings.append({
                        "type": "registry_artifacts",
                        "description": "Registry artifacts (fallback method)",
                        "details": {
                            "registry_keys": list(registry_keys)[:20]
                        }
                    })
                
                command_patterns = [
                    r'C:\\[^\s]+\.exe',
                    r'cmd\.exe /c [^\n]+',
                    r'powershell -[^\n]+'
                ]
                
                commands = set()
                for pattern in command_patterns:
                    matches = re.findall(pattern, strings_output.stdout)
                    commands.update(matches)
                
                if commands:
                    self.findings.append({
                        "type": "command_artifacts",
                        "description": "Command artifacts (fallback method)",
                        "details": {
                            "commands": list(commands)[:20]
                        }
                    })
            
        except Exception as e:
            logger.error("Error analyzing memory dump: %s", str(e))
            self.findings.append({
                "type": "error",
                "description": f"Error analyzing memory dump: {str(e)}"
            })
    
    def _analyze_disk_image(self, file_path: str) -> None:
        """Analyze a disk image file."""
        try:
            self.findings.append({
                "type": "info",
                "description": "Disk image file detected",
                "details": "Analyzing disk image for file system information, deleted files, and artifacts"
            })
            
            try:
                fsstat_output = subprocess.run(
                    ["fsstat", file_path],
                    capture_output=True, text=True, timeout=60
                )
                
                if fsstat_output.returncode == 0:
                    fs_info = {}
                    
                    fs_type_match = re.search(r'File System Type: (.+)', fsstat_output.stdout)
                    if fs_type_match:
                        fs_info["filesystem_type"] = fs_type_match.group(1).strip()
                    
                    vol_name_match = re.search(r'Volume Name: (.+)', fsstat_output.stdout)
                    if vol_name_match:
                        fs_info["volume_name"] = vol_name_match.group(1).strip()
                    
                    fs_info["metadata"] = {}
                    meta_matches = re.findall(r'([A-Za-z\s]+): (\d+)', fsstat_output.stdout)
                    for key, value in meta_matches:
                        fs_info["metadata"][key.strip()] = value
                    
                    self.findings.append({
                        "type": "filesystem_analysis",
                        "description": "File system analysis",
                        "details": fs_info
                    })
                
                mmls_output = subprocess.run(
                    ["mmls", file_path],
                    capture_output=True, text=True, timeout=60
                )
                
                if mmls_output.returncode == 0:
                    partitions = []
                    
                    for line in mmls_output.stdout.split('\n'):
                        if line and not line.startswith('Units') and not line.startswith('Slot'):
                            parts = line.split()
                            if len(parts) >= 5:
                                partitions.append({
                                    "slot": parts[0],
                                    "start_sector": parts[1],
                                    "end_sector": parts[2],
                                    "length": parts[3],
                                    "description": parts[4]
                                })
                    
                    self.findings.append({
                        "type": "partition_info",
                        "description": "Partition information",
                        "details": {
                            "partition_count": len(partitions),
                            "partitions": partitions
                        }
                    })
                
                fls_output = subprocess.run(
                    ["fls", "-rd", file_path],
                    capture_output=True, text=True, timeout=60
                )
                
                if fls_output.returncode == 0:
                    deleted_files = []
                    
                    for line in fls_output.stdout.split('\n'):
                        if line and '*' in line:  # Deleted files are marked with *
                            parts = line.split('*')
                            if len(parts) >= 2:
                                inode = parts[0].strip()
                                filename = parts[1].strip()
                                deleted_files.append({
                                    "inode": inode,
                                    "filename": filename
                                })
                    
                    self.findings.append({
                        "type": "deleted_files",
                        "description": "Deleted files analysis",
                        "details": {
                            "deleted_file_count": len(deleted_files),
                            "deleted_files": deleted_files[:20]  # Limit to first 20 files
                        }
                    })
                
                mactime_output = subprocess.run(
                    ["mactime", "-b", file_path + ".body"],
                    capture_output=True, text=True, timeout=60
                )
                
                if mactime_output.returncode == 0:
                    timeline_entries = []
                    
                    for line in mactime_output.stdout.split('\n')[:20]:  # Limit to first 20 entries
                        if line and not line.startswith('Date'):
                            parts = line.split(',')
                            if len(parts) >= 5:
                                timeline_entries.append({
                                    "date": parts[0],
                                    "size": parts[1],
                                    "activity": parts[2],
                                    "permissions": parts[3],
                                    "filename": parts[4]
                                })
                    
                    self.findings.append({
                        "type": "file_timeline",
                        "description": "File activity timeline",
                        "details": {
                            "timeline_entries": timeline_entries
                        }
                    })
                
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("The Sleuth Kit tools not available, using fallback method for disk image analysis")
                
                strings_output = subprocess.run(
                    ["strings", file_path], 
                    capture_output=True, text=True
                )
                
                fs_patterns = {
                    "ntfs": r'NTFS',
                    "fat": r'FAT(12|16|32)',
                    "ext": r'EXT[2-4]',
                    "hfs": r'HFS[+]?',
                    "ufs": r'UFS',
                    "reiserfs": r'ReiserFS',
                    "xfs": r'XFS'
                }
                
                detected_fs = []
                for fs_name, pattern in fs_patterns.items():
                    if re.search(pattern, strings_output.stdout, re.IGNORECASE):
                        detected_fs.append(fs_name)
                
                self.findings.append({
                    "type": "filesystem_analysis",
                    "description": "File system analysis (fallback method)",
                    "details": {
                        "possible_filesystems": detected_fs
                    }
                })
                
                file_path_patterns = [
                    r'[A-Z]:\\[^\s]+\.(exe|dll|sys|bat|cmd|ps1|vbs)',  # Windows paths
                    r'/etc/[^\s]+',  # Linux system config paths
                    r'/var/log/[^\s]+',  # Linux log paths
                    r'/home/[^\s]+',  # Linux home paths
                    r'/usr/[^\s]+'  # Linux usr paths
                ]
                
                file_paths = set()
                for pattern in file_path_patterns:
                    matches = re.findall(pattern, strings_output.stdout)
                    file_paths.update(matches)
                
                self.findings.append({
                    "type": "file_paths",
                    "description": "File paths detected (fallback method)",
                    "details": {
                        "file_path_count": len(file_paths),
                        "file_paths": list(file_paths)[:20]  # Limit to first 20 paths
                    }
                })
                
                registry_pattern = r'HKEY_[A-Z_]+\\[^\s]+'
                registry_keys = set(re.findall(registry_pattern, strings_output.stdout))
                
                if registry_keys:
                    self.findings.append({
                        "type": "registry_artifacts",
                        "description": "Registry artifacts (fallback method)",
                        "details": {
                            "registry_key_count": len(registry_keys),
                            "registry_keys": list(registry_keys)[:20]  # Limit to first 20 keys
                        }
                    })
                
                log_patterns = [
                    r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]',  # Common log timestamp format
                    r'(ERROR|WARNING|INFO|DEBUG):',  # Common log level indicators
                    r'Exception in thread'  # Exception indicators
                ]
                
                log_entries = set()
                for pattern in log_patterns:
                    for line in strings_output.stdout.split('\n'):
                        if re.search(pattern, line):
                            log_entries.add(line.strip())
                
                if log_entries:
                    self.findings.append({
                        "type": "log_artifacts",
                        "description": "Log artifacts (fallback method)",
                        "details": {
                            "log_entry_count": len(log_entries),
                            "log_entries": list(log_entries)[:20]  # Limit to first 20 entries
                        }
                    })
            
        except Exception as e:
            logger.error("Error analyzing disk image: %s", str(e))
            self.findings.append({
                "type": "error",
                "description": f"Error analyzing disk image: {str(e)}"
            })
    
    def _analyze_image(self, file_path: str) -> None:
        """Analyze an image file for steganography."""
        try:
            self.findings.append({
                "type": "info",
                "description": "Image file detected",
                "details": "Analyzing image for metadata and potential hidden data"
            })
            
            try:
                exif_output = subprocess.run(
                    ["exiftool", file_path],
                    capture_output=True, text=True, timeout=30
                )
                
                if exif_output.returncode == 0:
                    exif_data = {}
                    creation_info = {}
                    geolocation = {}
                    
                    for line in exif_output.stdout.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if any(time_key in key.lower() for time_key in ['create', 'date', 'time', 'modified']):
                                creation_info[key] = value
                            
                            elif any(geo_key in key.lower() for geo_key in ['gps', 'latitude', 'longitude', 'location']):
                                geolocation[key] = value
                            
                            exif_data[key] = value
                    
                    self.findings.append({
                        "type": "metadata_analysis",
                        "description": "Metadata analysis",
                        "details": {
                            "exif_data": exif_data,
                            "creation_info": creation_info,
                            "geolocation": geolocation
                        }
                    })
            
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("exiftool not available, using fallback method for metadata analysis")
                
                file_output = subprocess.run(
                    ["file", file_path],
                    capture_output=True, text=True
                )
                
                stat_output = subprocess.run(
                    ["stat", file_path],
                    capture_output=True, text=True
                )
                
                metadata = {
                    "file_info": file_output.stdout.strip() if file_output.returncode == 0 else "Unknown",
                    "file_stats": {}
                }
                
                if stat_output.returncode == 0:
                    for line in stat_output.stdout.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata["file_stats"][key.strip()] = value.strip()
                
                self.findings.append({
                    "type": "metadata_analysis",
                    "description": "Metadata analysis (fallback method)",
                    "details": metadata
                })
            
            try:
                steg_info = subprocess.run(
                    ["steghide", "info", file_path],
                    capture_output=True, text=True, input=b'\n', timeout=30
                )
                
                steganography_results = {
                    "hidden_data_detected": False,
                    "embedded_data_size": None,
                    "encryption": None
                }
                
                if "embedded" in steg_info.stdout:
                    steganography_results["hidden_data_detected"] = True
                    
                    size_match = re.search(r'capacity: ([\d.]+) [KMG]?B', steg_info.stdout)
                    if size_match:
                        steganography_results["embedded_data_size"] = size_match.group(1)
                    
                    if "encrypted" in steg_info.stdout:
                        steganography_results["encryption"] = "Yes"
                
                self.findings.append({
                    "type": "steganography_analysis",
                    "description": "Steganography analysis",
                    "details": steganography_results
                })
                
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("steghide not available, using fallback method for steganography analysis")
                
                strings_output = subprocess.run(
                    ["strings", file_path],
                    capture_output=True, text=True
                )
                
                suspicious_patterns = [
                    r'password',
                    r'secret',
                    r'hidden',
                    r'PK\x03\x04',  # ZIP file signature
                    r'%PDF',         # PDF file signature
                    r'\x50\x4B\x03\x04'  # ZIP file signature in hex
                ]
                
                suspicious_strings = []
                for pattern in suspicious_patterns:
                    matches = re.findall(pattern, strings_output.stdout, re.IGNORECASE)
                    if matches:
                        suspicious_strings.extend(matches)
                
                file_size = os.path.getsize(file_path)
                file_info = subprocess.run(
                    ["file", file_path],
                    capture_output=True, text=True
                )
                
                dimensions_match = re.search(r'(\d+)\s*x\s*(\d+)', file_info.stdout)
                unusual_size = False
                
                if dimensions_match:
                    width = int(dimensions_match.group(1))
                    height = int(dimensions_match.group(2))
                    expected_size_range = (width * height * 3 * 0.5, width * height * 4 * 1.5)  # Rough estimate
                    
                    if file_size < expected_size_range[0] or file_size > expected_size_range[1]:
                        unusual_size = True
                
                self.findings.append({
                    "type": "steganography_analysis",
                    "description": "Steganography analysis (fallback method)",
                    "details": {
                        "suspicious_strings_found": len(suspicious_strings) > 0,
                        "suspicious_strings": suspicious_strings[:10],
                        "unusual_file_size": unusual_size,
                        "file_size": file_size
                    }
                })
            
        except Exception as e:
            logger.error("Error analyzing image: %s", str(e))
            self.findings.append({
                "type": "error",
                "description": f"Error analyzing image: {str(e)}"
            })
    
    def _analyze_general_file(self, file_path: str) -> None:
        """Perform general analysis on a file."""
        try:
            result = subprocess.run(["strings", file_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                strings_output = result.stdout
                
                patterns = {
                    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                    "url": r'https?://[^\s]+',
                    "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                    "flag_format": r'flag\{[^}]+\}|CTF\{[^}]+\}',
                    "api_key": r'[a-zA-Z0-9]{32,}',
                    "password": r'password\s*[=:]\s*[^\s]+',
                    "private_key": r'-----BEGIN (\w+) PRIVATE KEY-----'
                }
                
                for pattern_name, pattern in patterns.items():
                    matches = re.findall(pattern, strings_output)
                    if matches:
                        self.findings.append({
                            "type": f"found_{pattern_name}",
                            "description": f"Found potential {pattern_name.replace('_', ' ')}",
                            "details": matches[:10]  # Limit to first 10 matches
                        })
            
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                entropy = 0
                if data:
                    byte_counts = {}
                    for byte in data:
                        if byte in byte_counts:
                            byte_counts[byte] += 1
                        else:
                            byte_counts[byte] = 1
                    
                    file_size = len(data)
                    for count in byte_counts.values():
                        probability = count / file_size
                        entropy -= probability * (math.log(probability) / math.log(2))
                
                entropy_interpretation = "Low (likely uncompressed/unencrypted)"
                if entropy > 7.0:
                    entropy_interpretation = "High (likely encrypted or compressed)"
                elif entropy > 5.0:
                    entropy_interpretation = "Medium (possibly compressed or encoded)"
                
                self.findings.append({
                    "type": "entropy_analysis",
                    "description": "File entropy analysis",
                    "details": {
                        "entropy_value": entropy,
                        "interpretation": entropy_interpretation
                    }
                })
            except Exception as entropy_error:
                logger.error("Error calculating entropy: %s", str(entropy_error))
                self.findings.append({
                    "type": "entropy_analysis",
                    "description": "File entropy analysis",
                    "details": f"Error calculating entropy: {str(entropy_error)}"
                })
            
            try:
                file_type = subprocess.run(
                    ["file", "-b", file_path],
                    capture_output=True, text=True
                )
                
                with open(file_path, 'rb') as f:
                    header = f.read(8).hex()
                
                signatures = {
                    "4d5a": "Windows executable (MZ)",
                    "504b0304": "ZIP archive",
                    "89504e47": "PNG image",
                    "ffd8ffe0": "JPEG image",
                    "25504446": "PDF document",
                    "7f454c46": "ELF executable",
                    "cafebabe": "Java class file",
                    "52617221": "RAR archive",
                    "1f8b0808": "GZIP archive"
                }
                
                detected_type = None
                for signature, file_desc in signatures.items():
                    if header.startswith(signature.lower()):
                        detected_type = file_desc
                        break
                
                # Check for inconsistencies between file command and signature
                inconsistent = False
                if detected_type:
                    for key in signatures.values():
                        if key.split()[0].lower() in file_type.stdout.lower() and key != detected_type:
                            inconsistent = True
                            break
                
                self.findings.append({
                    "type": "signature_analysis",
                    "description": "File signature analysis",
                    "details": {
                        "file_command_type": file_type.stdout.strip(),
                        "header_signature": header[:8],
                        "detected_type_from_signature": detected_type,
                        "inconsistent": inconsistent
                    }
                })
                
                if inconsistent:
                    self.findings.append({
                        "type": "warning",
                        "description": "Possible file type spoofing detected",
                        "details": "The file extension or reported type does not match the file signature"
                    })
                
            except Exception as sig_error:
                logger.error("Error analyzing file signature: %s", str(sig_error))
                self.findings.append({
                    "type": "signature_analysis",
                    "description": "File signature analysis",
                    "details": f"Error analyzing file signature: {str(sig_error)}"
                })
            
        except Exception as e:
            logger.error("Error performing general file analysis: %s", str(e))
            self.findings.append({
                "type": "error",
                "description": f"Error performing general file analysis: {str(e)}"
            })
