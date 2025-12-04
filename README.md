# DB Auto Backup

Automatically backs up PostgreSQL or SQLite every 24 hours  
Keeps only last 7 backups · Sends Telegram alert on success/failure

Perfect for freelancers, startups, and personal projects.

```bash
python backup.py --db "postgresql://user:pass@localhost/mydb" --token YOUR_BOT_TOKEN --chat YOUR_CHAT_ID
