import streamlit as st
from datetime import date, datetime, timedelta
import shutil
import os
import json
import time
import threading

# Global Constants
BACKUP_LOCATION = r'C:\Users\londh\OneDrive\Desktop\SSPRG\BackupSpace'
BACKUP_LOG = os.path.join(BACKUP_LOCATION, "backup_log.json")
SCHEDULE_INTERVAL_HOURS = 24

# Load or create backup log
def load_backup_log():
    if os.path.exists(BACKUP_LOG):
        with open(BACKUP_LOG, 'r') as f:
            return json.load(f)
    return {}

def save_backup_log(log_data):
    with open(BACKUP_LOG, 'w') as f:
        json.dump(log_data, f, indent=4)

# Incremental backup
def incremental_backup(source_folder, destination):
    log = load_backup_log()
    changed_files = []

    for root, _, files in os.walk(source_folder):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, source_folder)
            mod_time = os.path.getmtime(full_path)

            dest_path = os.path.join(destination, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            if rel_path not in log or mod_time > log[rel_path]:
                shutil.copy2(full_path, dest_path)
                log[rel_path] = mod_time
                changed_files.append(rel_path)
            else:
                # Copy unchanged files as well
                shutil.copy2(full_path, dest_path)

    save_backup_log(log)
    return changed_files


# Auto backup scheduler
def schedule_auto_backup(source_folder):
    def run_backup():
        while True:
            now = datetime.now()
            backup_folder = os.path.join(BACKUP_LOCATION, f"{now.strftime('%Y.%m.%d_%H.%M')}_Auto_Backup")
            os.makedirs(backup_folder, exist_ok=True)
            incremental_backup(source_folder, backup_folder)
            shutil.make_archive(backup_folder + "_compressed", 'zip', backup_folder)
            shutil.rmtree(backup_folder)
            print(f"✅ Auto backup completed at {now}")
            time.sleep(SCHEDULE_INTERVAL_HOURS * 3600)

    t = threading.Thread(target=run_backup)
    t.daemon = True
    t.start()

# GUI Section

def About():
    st.title("System Level Backup Utility")
    st.write("*A powerful tool that performs system-wide backups, allowing you to secure your data with ease and flexibility.*")
    st.subheader("Key Features")
    st.markdown("""
        <style>
            .st-emotion-cache-mtjnbi{
                padding-top:6rem;
            }
            .card {
                padding: 20px;
                background-color: #f0f0f0;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                text-align: center;
                font-size: 18px;
                width: 330px;
                text-align:left;
                background-color:white;
            }
        </style>
        <div style='display:flex; gap:20px;flex-wrap:wrap;'>
            <div class='card'>
                🔄<br> Full System Backup <br><p style='font-size:13px'> Backup entire directories or selected folders with a single click.</p>
            </div>
            <div class='card'>
                📂<br> Custom Folder Selection <br><p style='font-size:13px'>Choose specific files or directories to include in the backup.</p>
            </div>
             <div class='card'>
                ⏱️<br>Incremental Backups<br><p style='font-size:13px'>Save time and storage by backing up only the files that have changed.</p>
            </div>
             <div class='card'>
                💾<br>Restore from Backup<br><p style='font-size:13px'>Easily restore files or folders to their original state.</p>
            </div>
             <div class='card'>
                🛠️<br>Scheduled Backups<br><p style='font-size:13px'>Maintain and view a history of all backup operations with timestamps.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
#backup file
def BackupFile():
    st.header("🔒 Backup File")
    file = st.file_uploader("Choose file to back up")
    if st.button("Backup Now"):
        if file:
            d2 = str(date.today()).replace('-', '.')
            filename = f"{d2}_{file.name}"
            path = os.path.join(BACKUP_LOCATION, filename)
            with open(path, 'wb') as f:
                f.write(file.read())
            zip_path = shutil.make_archive(path + "_compressed", 'zip', BACKUP_LOCATION, filename)
            os.remove(path)
            st.success(f"✅ File backed up and compressed at: {zip_path}")
        else:
            st.warning("Please select a file.")

def BackupFolder():
    st.header("📁 Incremental Folder Backup")
    folder = st.text_input("Enter folder path to back up")
    if st.button("Start Backup"):
        if os.path.isdir(folder):
            d2 = str(date.today()).replace('-', '.')
            dest = os.path.join(BACKUP_LOCATION, f"{d2}_Folder_Backup")
            os.makedirs(dest, exist_ok=True)
            changed_files = incremental_backup(folder, dest)
            if changed_files:
                zip_path = shutil.make_archive(dest + "_compressed", 'zip', dest)
                shutil.rmtree(dest)
                st.success(f"✅ {len(changed_files)} files backed up and zipped.")
                st.write("Changed files:")
                for f in changed_files:
                    st.markdown(f"- {f}")
                st.write(f"📦 Backup saved to: {zip_path}")
            else:
                st.info("No changes since last backup.")
        else:
            st.error("Invalid folder path.")

def Restore():
    st.header("📤 Restore from Backup")
    zips = [f for f in os.listdir(BACKUP_LOCATION) if f.endswith(".zip")]
    if zips:
        selected = st.selectbox("Select backup ZIP:", zips)
        dest = st.text_input("Enter restore path:")
        if st.button("Restore Now"):
            if os.path.exists(os.path.join(BACKUP_LOCATION, selected)) and os.path.isdir(dest):
                shutil.unpack_archive(os.path.join(BACKUP_LOCATION, selected), dest)
                st.success("Backup restored.")
            else:
                st.error("Invalid file or destination path.")
    else:
        st.warning("No backup ZIPs found.")

def Schedule():
    st.header("🕒 Scheduled Backup")
    folder = st.text_input("Enter folder path to auto-backup:")
    if st.button("Enable Auto Backup"):
        if os.path.isdir(folder):
            schedule_auto_backup(folder)
            st.success(f"✅ Auto-backup started every {SCHEDULE_INTERVAL_HOURS} hours.")
        else:
            st.error("Invalid folder path.")

def History():
    st.header("📜 Backup History")
    if os.path.exists(BACKUP_LOG):
        log = load_backup_log()
        for f, t in log.items():
            st.markdown(f"- {f} last modified at {datetime.fromtimestamp(t)}")
    else:
        st.info("No backup history yet.")

# Main Function
def main():
    st.sidebar.title("Backup Utility Menu")
    page = st.sidebar.radio("Go to", ("About", "File Backup", "Directory Backup", "Restore", "Scheduled Backup", "History"))
    if page == "About":
        About()
    elif page == "File Backup":
        BackupFile()
    elif page == "Directory Backup":
        BackupFolder()
    elif page == "Restore":
        Restore()
    elif page == "Scheduled Backup":
        Schedule()
    elif page == "History":
        History()

main()