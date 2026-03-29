# scripts/backup.py
#!/usr/bin/env python
import os
import sys
import subprocess
import gzip
import shutil
from datetime import datetime
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def create_backup(backup_dir="backups"):
    """Create database backup"""
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"theo_backup_{timestamp}.sql")
    compressed_file = f"{backup_file}.gz"
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return False
    
    print(f"💾 Starting database backup...")
    print(f"   Output: {compressed_file}")
    
    try:
        # Use pg_dump to backup
        cmd = f"pg_dump '{DATABASE_URL}'"
        
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, shell=True, stdout=f, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print(f"❌ Backup failed: {result.stderr.decode()}")
            return False
        
        # Compress the backup
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        os.remove(backup_file)
        
        # Get file size
        size_bytes = os.path.getsize(compressed_file)
        size_mb = size_bytes / (1024 * 1024)
        
        print(f"✅ Backup successful!")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   File: {compressed_file}")
        
        # Clean up old backups (keep last 30 days)
        clean_old_backups(backup_dir, days=30)
        
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def clean_old_backups(backup_dir, days=30):
    """Delete backups older than specified days"""
    import time
    
    now = time.time()
    cutoff = now - (days * 86400)
    
    for filename in os.listdir(backup_dir):
        if filename.startswith("theo_backup_") and filename.endswith(".gz"):
            filepath = os.path.join(backup_dir, filename)
            if os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
                print(f"   Removed old backup: {filename}")

def list_backups(backup_dir="backups"):
    """List available backups"""
    if not os.path.exists(backup_dir):
        print("No backups found")
        return
    
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.startswith("theo_backup_") and filename.endswith(".gz"):
            filepath = os.path.join(backup_dir, filename)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            backups.append((filename, size_mb, mtime))
    
    if not backups:
        print("No backups found")
        return
    
    backups.sort(key=lambda x: x[2], reverse=True)
    
    print("\n📋 Available Backups:")
    print("-" * 60)
    for filename, size_mb, mtime in backups:
        print(f"  {mtime.strftime('%Y-%m-%d %H:%M:%S')} - {filename} ({size_mb:.2f} MB)")

def restore_backup(backup_file, backup_dir="backups"):
    """Restore from backup"""
    if not os.path.exists(backup_file):
        backup_file = os.path.join(backup_dir, backup_file)
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return False
    
    print(f"🔄 Restoring from: {backup_file}")
    print("⚠️  This will overwrite your current database!")
    confirm = input("Are you sure? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("Restore cancelled")
        return False
    
    try:
        # Decompress and restore
        with gzip.open(backup_file, 'rb') as f_in:
            with open('temp_restore.sql', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        cmd = f"psql '{DATABASE_URL}' < temp_restore.sql"
        result = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
        
        os.remove('temp_restore.sql')
        
        if result.returncode != 0:
            print(f"❌ Restore failed: {result.stderr.decode()}")
            return False
        
        print("✅ Restore successful!")
        return True
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="THEO Database Backup Tool")
    parser.add_argument("action", choices=["backup", "list", "restore"], help="Action to perform")
    parser.add_argument("--file", help="Backup file to restore (for restore action)")
    parser.add_argument("--dir", default="backups", help="Backup directory")
    
    args = parser.parse_args()
    
    if args.action == "backup":
        create_backup(args.dir)
    elif args.action == "list":
        list_backups(args.dir)
    elif args.action == "restore":
        if not args.file:
            print("❌ Please specify backup file with --file")
        else:
            restore_backup(args.file, args.dir)