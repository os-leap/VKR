import json
import os
import shutil
from datetime import datetime, timedelta
import zipfile
from pathlib import Path


class BackupSystem:
    def __init__(self, data_file="knowledge_base.json", backup_dir="backups"):
        self.data_file = data_file
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self):
        """Create a backup of the entire database with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_filename
        
        # Create a zip archive containing the data file and other important files
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the main data file
            if os.path.exists(self.data_file):
                zipf.write(self.data_file, os.path.basename(self.data_file))
            
            # Add audit logs
            audit_file = "audit_logs.json"
            if os.path.exists(audit_file):
                zipf.write(audit_file, os.path.basename(audit_file))
                
            # Add users file
            users_file = "users.json"
            if os.path.exists(users_file):
                zipf.write(users_file, os.path.basename(users_file))
                
        return str(backup_path)
    
    def list_backups(self):
        """List all available backups sorted by date (newest first)"""
        backups = []
        for file in self.backup_dir.glob("backup_*.zip"):
            timestamp_str = file.stem.replace("backup_", "")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                backups.append({
                    'filename': file.name,
                    'timestamp': timestamp,
                    'filepath': str(file),
                    'size': file.stat().st_size
                })
            except ValueError:
                continue
                
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def restore_backup(self, backup_filename):
        """Restore database from a specific backup"""
        backup_path = self.backup_dir / backup_filename
        if not backup_path.exists():
            return False
            
        try:
            # Extract the backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Extract to temporary location first
                temp_extract_dir = self.backup_dir / "temp_restore"
                temp_extract_dir.mkdir(exist_ok=True)
                
                zipf.extractall(temp_extract_dir)
                
                # Copy files back to original location
                for extracted_file in temp_extract_dir.glob("*"):
                    destination = Path(extracted_file.name)
                    shutil.copy2(extracted_file, destination)
                    
                # Clean up temporary directory
                shutil.rmtree(temp_extract_dir)
                
            return True
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def cleanup_old_backups(self, days_to_keep=7):
        """Remove backups older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        backups = self.list_backups()
        
        removed_count = 0
        for backup in backups:
            if backup['timestamp'] < cutoff_date:
                os.remove(backup['filepath'])
                removed_count += 1
                
        return removed_count


# Global backup system instance
backup_system = BackupSystem()


def create_daily_backup():
    """Function to create daily backup - can be scheduled"""
    try:
        backup_path = backup_system.create_backup()
        print(f"Daily backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"Failed to create daily backup: {e}")
        return False