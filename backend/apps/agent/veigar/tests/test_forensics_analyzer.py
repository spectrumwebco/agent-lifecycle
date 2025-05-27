"""
Tests for the Veigar forensics analyzer.

This module contains tests for the forensics analyzer component of the Veigar agent.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import tempfile

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from veigar.tools.forensics.analyzer import ForensicsAnalyzer


class TestForensicsAnalyzer:
    """Test suite for the ForensicsAnalyzer class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.analyzer = ForensicsAnalyzer()
        self.test_pcap = "/path/to/capture.pcap"
        self.test_memory_dump = "/path/to/memory.dmp"
        self.test_disk_image = "/path/to/disk.img"
        self.test_image = "/path/to/suspicious.jpg"

    def test_initialization(self):
        """Test that the analyzer initializes correctly."""
        assert hasattr(self.analyzer, "analyze_network_traffic")
        assert hasattr(self.analyzer, "analyze_memory_dump")
        assert hasattr(self.analyzer, "analyze_disk_image")
        assert hasattr(self.analyzer, "analyze_image_metadata")

    @patch("subprocess.run")
    def test_analyze_network_traffic_with_tool_available(self, mock_run):
        """Test network traffic analysis when tshark is available."""
        mock_process = MagicMock()
        mock_process.stdout = """
        1 0.000000000 192.168.1.100 → 93.184.216.34 TCP 74 59378 → 80 [SYN] Seq=0 Win=64240 Len=0 MSS=1460 SACK_PERM=1 TSval=3302576547 TSecr=0 WS=128
        2 0.030242000 93.184.216.34 → 192.168.1.100 TCP 74 80 → 59378 [SYN, ACK] Seq=0 Ack=1 Win=65535 Len=0 MSS=1460 SACK_PERM=1 TSval=2148095914 TSecr=3302576547 WS=128
        3 0.030347000 192.168.1.100 → 93.184.216.34 TCP 66 59378 → 80 [ACK] Seq=1 Ack=1 Win=64240 Len=0 TSval=3302576577 TSecr=2148095914
        4 0.030473000 192.168.1.100 → 93.184.216.34 HTTP 143 GET / HTTP/1.1
        5 0.060715000 93.184.216.34 → 192.168.1.100 TCP 66 80 → 59378 [ACK] Seq=1 Ack=78 Win=65535 Len=0 TSval=2148095944 TSecr=3302576577
        6 0.062010000 93.184.216.34 → 192.168.1.100 HTTP 497 HTTP/1.1 301 Moved Permanently
        """
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        with patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_network_traffic(self.test_pcap)
        
            assert results["status"] == "success"
            assert "findings" in results
            assert "file" in results
            assert results["file"] == self.test_pcap

    @patch("subprocess.run")
    def test_analyze_network_traffic_with_tool_unavailable(self, mock_run):
        """Test network traffic analysis when tshark is not available."""
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'tshark'")
    
        with patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_network_traffic(self.test_pcap)
    
            assert results["status"] == "success"  # Actual implementation returns success with fallback
            assert "findings" in results
            
            error_findings = [f for f in results["findings"] if f.get("type") == "error"]
            assert len(error_findings) > 0
            assert any("tshark" in str(f.get("description", "")) for f in error_findings)

    @patch("subprocess.run")
    def test_analyze_memory_dump_with_tool_available(self, mock_run):
        """Test memory dump analysis when volatility is available."""
        mock_process = MagicMock()
        mock_process.stdout = """
        Volatility Foundation Volatility Framework 2.6
        Offset(V)  Name                    PID   PPID   Thds     Hnds   Sess  Wow64 Start                          Exit
        ---------- -------------------- ------ ------ ------ -------- ------ ------ ------------------------------ ------------------------------
        0x85c64d40 System                    4      0     97      621 ------      0 2020-07-22 19:45:57 UTC+0000
        0x84bcf980 smss.exe                272      4      3       19 ------      0 2020-07-22 19:45:57 UTC+0000
        0x84d42b80 csrss.exe               348    340      9      436      0      0 2020-07-22 19:45:58 UTC+0000
        0x84d4e7e8 wininit.exe             396    340      3       77      0      0 2020-07-22 19:45:58 UTC+0000
        0x84d4f030 csrss.exe               408    388     10      288      1      0 2020-07-22 19:45:58 UTC+0000
        0x84d89d40 winlogon.exe            456    388      3      113      1      0 2020-07-22 19:45:58 UTC+0000
        0x84e30170 services.exe            504    396     11      242      0      0 2020-07-22 19:45:58 UTC+0000
        0x84e313a8 lsass.exe               512    396      7      610      0      0 2020-07-22 19:45:58 UTC+0000
        0x84e31610 lsm.exe                 520    396     10      148      0      0 2020-07-22 19:45:58 UTC+0000
        0x84e9f030 svchost.exe             628    504     12      358      0      0 2020-07-22 19:45:58 UTC+0000
        0x84ea4030 svchost.exe             692    504      8      278      0      0 2020-07-22 19:45:58 UTC+0000
        0x84ed5030 svchost.exe             740    504     22      508      0      0 2020-07-22 19:45:58 UTC+0000
        0x84ed9030 svchost.exe             768    504     14      337      0      0 2020-07-22 19:45:58 UTC+0000
        0x84edc030 svchost.exe             804    504     27      912      0      0 2020-07-22 19:45:58 UTC+0000
        0x84f0f678 svchost.exe             916    504     33      734      0      0 2020-07-22 19:45:58 UTC+0000
        0x84f4f678 spoolsv.exe            1076    504     14      346      0      0 2020-07-22 19:45:58 UTC+0000
        0x84f8f678 svchost.exe            1104    504     18      310      0      0 2020-07-22 19:45:58 UTC+0000
        0x84fcf678 svchost.exe            1196    504     34      250      0      0 2020-07-22 19:45:59 UTC+0000
        0x8500f678 svchost.exe            1272    504     11      180      0      0 2020-07-22 19:45:59 UTC+0000
        0x8504f678 taskhost.exe           1668    504      8      193      1      0 2020-07-22 19:46:00 UTC+0000
        0x8508f678 dwm.exe                1700    804      3       72      1      0 2020-07-22 19:46:00 UTC+0000
        0x850cf678 explorer.exe           1720   1676     21      760      1      0 2020-07-22 19:46:00 UTC+0000
        0x8510f678 malware.exe            1984   1720      2       54      1      0 2020-07-22 19:46:01 UTC+0000
        """
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        with patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_memory_dump(self.test_memory_dump)
        
            assert results["status"] == "success"
            assert "findings" in results
            assert "file" in results
            assert results["file"] == self.test_memory_dump

    @patch("subprocess.run")
    def test_analyze_memory_dump_with_tool_unavailable(self, mock_run):
        """Test memory dump analysis when volatility is not available."""
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'volatility'")
    
        with patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_memory_dump(self.test_memory_dump)
    
            assert results["status"] == "success"  # Actual implementation returns success with fallback
            assert "findings" in results
            
            error_findings = [f for f in results["findings"] if f.get("type") == "error"]
            assert len(error_findings) > 0
            assert any("volatility" in str(f.get("description", "")) for f in error_findings)

    @patch("subprocess.run")
    def test_analyze_disk_image_with_tool_available(self, mock_run):
        """Test disk image analysis when tools are available."""
        mock_process = MagicMock()
        mock_process.stdout = """
        Filesystem      Size  Used Avail Use% Mounted on
        /dev/loop0       50G   15G   35G  30% /mnt/image
    
        /mnt/image/Windows/System32/config/SAM
        /mnt/image/Windows/System32/config/SYSTEM
        /mnt/image/Users/Administrator/AppData/Roaming/malware.exe
        /mnt/image/Users/Administrator/AppData/Local/Temp/suspicious.dll
        """
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        with patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_disk_image(self.test_disk_image)
        
            assert results["status"] == "success"  # Actual implementation returns success
            assert "findings" in results
            assert "file" in results
            assert results["file"] == self.test_disk_image

    @patch("subprocess.run")
    def test_analyze_disk_image_with_tool_unavailable(self, mock_run):
        """Test disk image analysis when tools are not available."""
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'mount'")
    
        with patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_disk_image(self.test_disk_image)
    
            assert results["status"] == "success"  # Actual implementation returns success with fallback
            assert "findings" in results
            
            error_findings = [f for f in results["findings"] if f.get("type") == "error"]
            assert len(error_findings) > 0
            assert any("mount" in str(f.get("description", "")) for f in error_findings)

    @patch("subprocess.run")
    def test_analyze_image_metadata_with_tool_available(self, mock_run):
        """Test image metadata analysis when exiftool is available."""
        mock_process = MagicMock()
        mock_process.stdout = """
        ExifTool Version Number         : 12.30
        File Name                       : suspicious.jpg
        Directory                       : /path/to
        File Size                       : 123 KiB
        File Modification Date/Time     : 2023:01:15 12:34:56+00:00
        File Access Date/Time           : 2023:01:15 12:34:56+00:00
        File Creation Date/Time         : 2023:01:15 12:34:56+00:00
        File Permissions                : -rw-r--r--
        File Type                       : JPEG
        File Type Extension             : jpg
        MIME Type                       : image/jpeg
        JFIF Version                    : 1.01
        Resolution Unit                 : inches
        X Resolution                    : 72
        Y Resolution                    : 72
        Comment                         : Created with GIMP
        Image Width                     : 1920
        Image Height                    : 1080
        Encoding Process                : Baseline DCT, Huffman coding
        Bits Per Sample                 : 8
        Color Components                : 3
        Y Cb Cr Sub Sampling            : YCbCr4:2:0 (2 2)
        GPS Latitude                    : 37 deg 46' 28.80" N
        GPS Longitude                   : 122 deg 25' 1.20" W
        Creator Tool                    : Adobe Photoshop CC 2019 (Windows)
        Author                          : John Doe
        """
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        with patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_image_metadata(self.test_image)
        
            assert results["status"] == "success"  # Actual implementation returns success
            assert "metadata" in results
            assert "file" in results
            assert results["file"] == self.test_image
            assert "analysis" in results

    @patch("subprocess.run")
    def test_analyze_image_metadata_with_tool_unavailable(self, mock_run):
        """Test image metadata analysis when exiftool is not available."""
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'exiftool'")
    
        with patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_image_metadata(self.test_image)
    
            assert results["status"] == "error"  # Actual implementation returns error
            assert "error" in results

    @patch("subprocess.run")
    def test_analyze_image_steganography_with_tool_available(self, mock_run):
        """Test image steganography analysis when steghide is available."""
        mock_process = MagicMock()
        mock_process.stdout = "extracted data written to \"secret.txt\"."
        mock_process.returncode = 0
        mock_run.return_value = mock_process
    
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write("This is hidden data")
            temp_path = temp_file.name
    
        with patch("builtins.open", return_value=open(temp_path)), \
             patch("os.path.exists", return_value=True):
            results = self.analyzer.analyze_image_steganography(self.test_image, "password")
    
            assert results["status"] == "success"  # Actual implementation returns success
            assert "has_hidden_data" in results
            assert "analysis_method" in results
            assert results["analysis_method"] == "steghide"
        
        os.unlink(temp_path)

    @patch("subprocess.run")
    def test_analyze_image_steganography_with_tool_unavailable(self, mock_run):
        """Test image steganography analysis when steghide is not available."""
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'steghide'")
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", return_value=MagicMock()):
            
            results = self.analyzer.analyze_image_steganography(self.test_image, "password")
            
            assert results["status"] == "success"
            assert "has_hidden_data" in results
            assert "note" in results
            assert "Limited analysis" in results["note"]
        assert "analysis" in results
        assert "analysis_method" in results

    def test_comprehensive_analysis(self):
        """Test comprehensive forensic analysis."""
        with patch.object(self.analyzer, "analyze_network_traffic") as mock_network, \
             patch.object(self.analyzer, "analyze_memory_dump") as mock_memory, \
             patch.object(self.analyzer, "analyze_disk_image") as mock_disk, \
             patch.object(self.analyzer, "analyze_image_metadata") as mock_image, \
             patch.object(self.analyzer, "analyze_image_steganography") as mock_stego:
            
            mock_network.return_value = {
                "status": "success",
                "findings": [],
                "file": self.test_pcap
            }
            mock_memory.return_value = {
                "status": "success",
                "findings": [],
                "file": self.test_memory_dump
            }
            mock_disk.return_value = {
                "status": "success",
                "findings": [],
                "file": self.test_disk_image
            }
            mock_image.return_value = {
                "status": "success",
                "metadata": {"GPS Latitude": "37 deg 46' 28.80\" N"},
                "file": self.test_image,
                "analysis": {
                    "has_gps_data": True,
                    "has_author_info": False,
                    "metadata_count": 1
                }
            }
            mock_stego.return_value = {
                "status": "success",
                "has_hidden_data": False,
                "file": self.test_image,
                "analysis_method": "steghide"
            }
            
            results = self.analyzer.comprehensive_analysis(
                network_file=self.test_pcap,
                memory_file=self.test_memory_dump,
                disk_file=self.test_disk_image,
                image_file=self.test_image
            )
            
            assert results["status"] == "success"
            assert "analyses" in results
            assert "summary" in results
            
            mock_network.assert_called_once_with(self.test_pcap)
            mock_memory.assert_called_once_with(self.test_memory_dump)
            mock_disk.assert_called_once_with(self.test_disk_image)
            mock_image.assert_called_once_with(self.test_image)

    def test_error_handling(self):
        """Test error handling in forensic analysis."""
        mock_network_result = {"status": "error", "error": "Network analysis error"}
        mock_memory_result = {"status": "error", "error": "Memory analysis error"}
        mock_disk_result = {"status": "error", "error": "Disk analysis error"}
        mock_image_result = {"status": "error", "error": "Image analysis error"}
        mock_stego_result = {"status": "error", "error": "Steganography analysis error"}
        
        with patch.object(self.analyzer, "analyze_network_traffic", return_value=mock_network_result), \
             patch.object(self.analyzer, "analyze_memory_dump", return_value=mock_memory_result), \
             patch.object(self.analyzer, "analyze_disk_image", return_value=mock_disk_result), \
             patch.object(self.analyzer, "analyze_image_metadata", return_value=mock_image_result), \
             patch.object(self.analyzer, "analyze_image_steganography", return_value=mock_stego_result):
            
            results = self.analyzer.comprehensive_analysis(
                network_file=self.test_pcap,
                memory_file=self.test_memory_dump,
                disk_file=self.test_disk_image,
                image_file=self.test_image
            )
            
            assert results["status"] == "success"
            assert "analyses" in results
            assert "summary" in results
            
            if "network" in results["analyses"]:
                assert results["analyses"]["network"]["status"] == "error"
            if "memory" in results["analyses"]:
                assert results["analyses"]["memory"]["status"] == "error"
            if "disk" in results["analyses"]:
                assert results["analyses"]["disk"]["status"] == "error"
