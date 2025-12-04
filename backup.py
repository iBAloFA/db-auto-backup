import typer, os, datetime, subprocess, glob
from telegram import Bot
import schedule, time

app = typer.Typer(help="Daily database backup with Telegram alerts")

def send_telegram(message: str, token: str, chat_id: str):
    try:
        bot = Bot(token=token)
        bot.send_message(chat_id=chat_id, text=message)
    except:
        pass  # Silent fail if Telegram down

def backup_postgres(db_url: str, backup_dir: str = "backups"):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = f"{backup_dir}/backup_{timestamp}.sql"

    cmd = f"pg_dump \"{db_url}\" > \"{backup_file}\""
    result = subprocess.run(cmd, shell=True)
    
    return backup_file, result.returncode == 0

def backup_sqlite(db_path: str, backup_dir: str = "backups"):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = f"{backup_dir}/backup_{timestamp}.db"
    
    import shutil
    shutil.copy2(db_path, backup_file)
    return backup_file, True

def rotate_backups(backup_dir: str = "backups", keep: int = 7):
    files = sorted(glob.glob(f"{backup_dir}/*"), key=os.path.getmtime, reverse=True)
    for old_file in files[keep:]:
        os.remove(old_file)

@app.command()
def run(
    db: str = typer.Option(..., "--db", help="Database URL or SQLite path"),
    token: str = typer.Option(..., "--token", help="Telegram bot token"),
    chat: str = typer.Option(..., "--chat", help="Your Telegram chat ID"),
    interval: int = typer.Option(24, help="Backup every X hours")
):
    """Start the backup scheduler"""
    typer.echo("DB Auto Backup started – press Ctrl+C to stop")

    def job():
        typer.echo(f"Running backup at {datetime.datetime.now()}...")
        success = False
        backup_file = ""

        if db.startswith("postgres://") or db.startswith("postgresql://"):
            backup_file, success = backup_postgres(db)
        elif db.endswith(".db") or db.endswith(".sqlite3"):
            backup_file, success = backup_sqlite(db)

        size = os.path.getsize(backup_file) / (1024*1024) if success else 0
        rotate_backups()

        if success:
            send_telegram(f"Backup successful!\nFile: {os.path.basename(backup_file)}\nSize: {size:.1f} MB", token, chat)
            typer.echo("Backup completed & alert sent")
        else:
            send_telegram("BACKUP FAILED! Check server immediately!", token, chat)
            typer.echo("Backup failed!")

    # Run now + schedule
    job()
    schedule.every(interval).hours.do(job)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    app()
