import json,random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker
fake = Faker("ru_RU")

SERVERS = ["web01","web02","db01","db02","auth01","cache01","backup01","mail01", "api01","api02",]
LEVELS = ["INFO", "WARNING", "ERROR"]
MESSAGES = {"INFO": [
        "Service started successfully",
        "User session created",
        "Scheduled task completed",
        "Configuration loaded",
        "Health check passed",
        "Connection pool initialized",
        "Backup verification completed",
        "Request processed successfully",
        "Cache warmed up",
        "Database replication status normal",
    ],
    "WARNING": [
        "High memory usage detected",
        "Disk space usage above threshold",
        "Slow response time detected",
        "Failed login attempt",
        "Temporary network latency detected",
        "SSL certificate will expire soon",
        "Retrying connection to remote host",
        "CPU load is above normal",
        "Unexpected response code from upstream",
        "Queue length is growing",
    ],
    "ERROR": [
        "Database connection failed",
        "Service unavailable",
        "Timeout while connecting to upstream",
        "Authentication service error",
        "Failed to write to disk",
        "Backup job failed",
        "Unhandled exception in worker process",
        "Failed to send email notification",
        "Replication lag exceeded limit",
        "Permission denied while accessing file",
    ],
}


def generate_logs(file_path: str, count: int = 1000):
    if count <= 0:
        raise ValueError("Количество записей должно быть больше нуля")

    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    start_date = datetime(2026, 6, 10, 0, 0, 0)

    with output_path.open("w", encoding="utf-8") as file:
        for index in range(count):
            level = random.choices(LEVELS,weights=[60, 30, 10],k=1)[0]

            #гарант ошибок у сервера
            if index % 100 == 0:
                server = "web01"
                level = "ERROR"
            else:
                server = random.choice(SERVERS)

            log_date = start_date + timedelta(
                minutes=random.randint(0, 60 * 24 * 30),
                seconds=random.randint(0, 59)
            )

            log_record = {
                "date": log_date.strftime("%Y-%m-%d %H:%M:%S"),
                "server": server,
                "level": level,
                "message": random.choice(MESSAGES[level]),
            }
            file.write(json.dumps(log_record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    generate_logs("../data/logs.jsonl", count=1000)
    print("Файл data/logs.jsonl успешно создан")