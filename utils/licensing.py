import subprocess
import hashlib
import os
from pathlib import Path
from loguru import logger
from config.app_config import AppConfig

class LicenseManager:
    """Handles software licensing and machine-specific activation"""
    
    @staticmethod
    def _get_license_file_path():
        """Get the path to the license key file in AppData"""
        data_dir = AppConfig.get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "license.key"

    @staticmethod
    def get_machine_id():
        """Retrieve a unique identifier for the current hardware"""
        try:
            # Try getting UUID via powershell
            cmd = 'Get-CimInstance -Class Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID'
            uuid = subprocess.check_output(['powershell', '-Command', cmd], text=True).strip()
            if uuid:
                return uuid
        except Exception as e:
            logger.warning(f"Failed to get machine UUID via PowerShell: {e}")
            
        # Fallback: Hash of environment variables and basic info
        fallback_str = os.environ.get('COMPUTERNAME', '') + os.environ.get('PROCESSOR_IDENTIFIER', '')
        return hashlib.sha256(fallback_str.encode()).hexdigest()

    @staticmethod
    def generate_license_hash(machine_id, owner_name="Joachim Korang Amponsah"):
        """Generate a valid license key based on machine ID and owner"""
        # A simple hashing mechanism (can be made more complex)
        salt = "POS_SYSTEM_2026_SECRET_SALT"
        input_str = f"{machine_id}:{owner_name}:{salt}"
        return hashlib.sha256(input_str.encode()).hexdigest().upper()[:20]

    @staticmethod
    def verify_license():
        """Check if the software is activated on this machine"""
        license_file = LicenseManager._get_license_file_path()
        if not license_file.exists():
            return False, "License key missing."
            
        try:
            with open(license_file, 'r') as f:
                stored_key = f.read().strip()
                
            machine_id = LicenseManager.get_machine_id()
            valid_key = LicenseManager.generate_license_hash(machine_id)
            
            if stored_key == valid_key:
                return True, "Success"
            else:
                return False, "Invalid license key for this hardware."
        except Exception as e:
            return False, f"Verification error: {e}"

    @staticmethod
    def activate(key):
        """Save a new license key"""
        machine_id = LicenseManager.get_machine_id()
        valid_key = LicenseManager.generate_license_hash(machine_id)
        
        if key.strip().upper() == valid_key:
            license_file = LicenseManager._get_license_file_path()
            try:
                with open(license_file, 'w') as f:
                    f.write(valid_key)
                return True
            except Exception as e:
                logger.error(f"Failed to write license file: {e}")
                return False
        return False
