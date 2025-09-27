"""
System checker for setup wizard
"""

import subprocess
import shutil
import psutil
import os
import socket
from typing import List, Dict, Any
import logging

from .models import SystemCheckResult

logger = logging.getLogger(__name__)


class SystemChecker:
    """System requirements checker"""
    
    def __init__(self):
        self.required_ports = [3030, 4000, 5432, 6333, 8000, 8001, 8002, 9000, 9002]
    
    def check_docker_installation(self) -> bool:
        """Check if Docker is installed"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_docker_compose_installation(self) -> bool:
        """Check if Docker Compose is installed"""
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_nvidia_gpu(self) -> bool:
        """Check if NVIDIA GPU is available"""
        try:
            result = subprocess.run(['nvidia-smi'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_nvidia_docker(self) -> bool:
        """Check if NVIDIA Docker runtime is available"""
        try:
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True, timeout=10)
            return 'nvidia' in result.stdout.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_disk_space(self) -> float:
        """Check available disk space in GB"""
        try:
            disk_usage = psutil.disk_usage('/')
            return disk_usage.free / (1024**3)  # Convert to GB
        except Exception:
            return 0.0
    
    def check_memory(self) -> float:
        """Check available memory in GB"""
        try:
            memory = psutil.virtual_memory()
            return memory.total / (1024**3)  # Convert to GB
        except Exception:
            return 0.0
    
    def check_port_availability(self) -> List[int]:
        """Check which required ports are available"""
        available_ports = []
        
        for port in self.required_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    if result != 0:  # Port is available
                        available_ports.append(port)
            except Exception:
                available_ports.append(port)  # Assume available if check fails
        
        return available_ports
    
    def check_port_conflicts(self) -> List[str]:
        """Check for port conflicts and return details"""
        conflicts = []
        
        for port in self.required_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    if result == 0:  # Port is in use
                        # Try to get process info
                        try:
                            result = subprocess.run(['ss', '-tulpn', f'sport = :{port}'], 
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode == 0 and result.stdout.strip():
                                conflicts.append(f"Port {port}: {result.stdout.strip().split()[-1]}")
                            else:
                                conflicts.append(f"Port {port}: Unknown process")
                        except Exception:
                            conflicts.append(f"Port {port}: Process using port")
            except Exception:
                pass
        
        return conflicts
    
    def check_nvme_availability(self) -> bool:
        """Check if NVMe storage is available"""
        return os.path.exists('/mnt/nvme')
    
    def run_full_check(self) -> SystemCheckResult:
        """Run complete system check"""
        logger.info("Running system check...")
        
        docker_installed = self.check_docker_installation()
        docker_compose_installed = self.check_docker_compose_installation()
        nvidia_gpu_available = self.check_nvidia_gpu()
        nvidia_docker_available = self.check_nvidia_docker()
        disk_space_gb = self.check_disk_space()
        memory_gb = self.check_memory()
        ports_available = self.check_port_availability()
        conflicts = self.check_port_conflicts()
        
        logger.info(f"System check completed: Docker={docker_installed}, "
                   f"GPU={nvidia_gpu_available}, Disk={disk_space_gb:.1f}GB, "
                   f"Memory={memory_gb:.1f}GB")
        
        return SystemCheckResult(
            docker_installed=docker_installed,
            docker_compose_installed=docker_compose_installed,
            nvidia_gpu_available=nvidia_gpu_available,
            nvidia_docker_available=nvidia_docker_available,
            disk_space_gb=disk_space_gb,
            memory_gb=memory_gb,
            ports_available=ports_available,
            conflicts=conflicts
        )
