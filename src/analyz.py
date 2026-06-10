from __future__ import annotations
import json,logging
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict


logging.basicConfig(filename="../app.log", level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", encoding="utf-8", )

logger = logging.getLogger(__name__)

def nested_defaultdict() -> DefaultDict[str, list[str]]:
    return defaultdict(list)

class LogAnalyzer:
    VALID_LEVELS = {"INFO", "WARNING", "ERROR"}

    def __init__(self, file_path: str):

        self._file_path = file_path
        self._logs_by_server: DefaultDict[str, DefaultDict[str, list[str]]] = defaultdict(nested_defaultdict)
        self._report: dict[str, Any] = {}
        self._records_count = 0

        logger.info("Создан LogAnalyzer для файла: %s", file_path)

    @property
    def file_path(self) -> str:
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        if not value:
            raise ValueError("Путь к файлу не может быть пустым")
        self._file_path = value
        logger.info("Путь к файлу изменён на: %s", value)

    @property
    def records_count(self) -> int:

        return self._records_count

    @property
    def report(self) -> dict[str, Any]:
        return self._report

    def read_logs(self):
        path = Path(self._file_path)
        if not path.exists():
            logger.error("Файл не найден: %s", self._file_path)
            raise FileNotFoundError(f"Файл не найден: {self._file_path}")

        logger.info("Начато чтение файла: %s", self._file_path)

        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    logger.debug("Пропущена пустая строка: %s", line_number)
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as error:
                    logger.error("Ошибка JSON в строке %s файла %s",
                        line_number, self._file_path,)
                    raise ValueError(f"Повреждённый JSON в строке {line_number}") from error

    def _validate_log_record(self, record: dict[str, Any]) -> None:
        required_fields = {"date", "server", "level", "message"}
        if not required_fields.issubset(record):
            raise ValueError(f"Запись не содержит обязательные поля: {record}")
        if record["level"] not in self.VALID_LEVELS:
            raise ValueError(f"Недопустимый уровень сообщения: {record['level']}")

    def build_structure(self):
        self._logs_by_server = defaultdict(nested_defaultdict)
        self._records_count = 0

        logger.info("Начато построение структуры логов")

        for record in self.read_logs():
            self._validate_log_record(record)
            self.add_log(  date=record["date"],server=record["server"],level=record["level"],message=record["message"])
        logger.info("Структура логов построена. Записей обработано: %s", self._records_count)

    def add_log(self, date: str, server: str, level: str, message: str) -> None:
        if level not in self.VALID_LEVELS:
            logger.error("Попытка добавить лог с неверным уровнем: %s", level)
            raise ValueError(f"Недопустимый уровень сообщения: {level}")

        self._logs_by_server[server][level].append(message)
        self._records_count += 1

        logger.debug( "Добавлен лог: date=%s, server=%s, level=%s, message=%s", date,server,level,message)

    def get_errors_for_server(self, server: str = "web01") -> list[str]:
        if server not in self._logs_by_server:
            logger.info("Сервер %s не найден. ERROR-сообщений нет.", server)
            return []

        errors = list(self._logs_by_server[server].get("ERROR", []))
        logger.info("Получены ERROR-сообщения для сервера %s", server)
        return errors

    def count_messages_by_level(self) -> dict[str, dict[str, int]]:
        result = {}

        for server, levels in self._logs_by_server.items():
            result[server] = {
                "INFO": len(levels["INFO"]),
                "WARNING": len(levels["WARNING"]),
                "ERROR": len(levels["ERROR"]),
            }

        logger.info("Выполнен подсчёт сообщений по уровням")
        return result

    def find_server_with_max_warnings(self) -> dict[str, Any]:
        if not self._logs_by_server:
            logger.warning("Попытка найти максимум WARNING в пустой структуре")
            return {"server": None, "warnings_count": 0}

        max_server = None
        max_count = -1

        for server, levels in self._logs_by_server.items():
            warnings_count = len(levels["WARNING"])

            if warnings_count > max_count:
                max_server = server
                max_count = warnings_count

        logger.info("Сервер с максимальным количеством WARNING: %s (%s)", max_server, max_count,)

        return {
            "server": max_server,
            "warnings_count": max_count,
        }

    def create_report(self) -> dict[str, Any]:
        self._report = {
            "total_records": self._records_count,
            "errors_for_web01": self.get_errors_for_server("web01"),
            "messages_count_by_server": self.count_messages_by_level(),
            "server_with_max_warnings": self.find_server_with_max_warnings(),
        }

        logger.info("Аналитический отчёт сформирован")
        return self._report

    def export_report(self, output_path: str) -> None:
        if not self._report:
            self.create_report()

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(self._report, file, ensure_ascii=False, indent=4)

        logger.info("Отчёт сохранён в файл: %s", output_path)

    def to_dict(self) -> dict[str, Any]:
        logs_as_dict = {
            server: {
                level: list(messages)
                for level, messages in levels.items()
            }
            for server, levels in self._logs_by_server.items()
        }

        return {
            "file_path": self._file_path,
            "logs_by_server": logs_as_dict,
            "records_count": self._records_count,
            "report": self._report,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LogAnalyzer:
        analyzer = cls(data["file_path"])
        analyzer._records_count = data.get("records_count", 0)
        analyzer._report = data.get("report", {})

        logs_by_server = defaultdict(nested_defaultdict)

        for server, levels in data.get("logs_by_server", {}).items():
            for level, messages in levels.items():
                logs_by_server[server][level] = list(messages)

        analyzer._logs_by_server = logs_by_server

        logger.info("Объект LogAnalyzer восстановлен из словаря")
        return analyzer

    def save_state(self, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)

        logger.info("Состояние анализатора сохранено в файл: %s", output_path)

    @classmethod
    def load_state(cls, input_path: str) -> LogAnalyzer:
        path = Path(input_path)

        if not path.exists():
            logger.error("Файл состояния не найден: %s", input_path)
            raise FileNotFoundError(f"Файл состояния не найден: {input_path}")

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            logger.error("Повреждённый JSON в файле состояния: %s", input_path)
            raise ValueError("Файл состояния содержит повреждённый JSON") from error

        logger.info("Состояние анализатора загружено из файла: %s", input_path)
        return cls.from_dict(data)