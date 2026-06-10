import json,pytest
from src.analyz  import LogAnalyzer

#тестовые логи
def create_test_log_file(tmp_path, records):
    file_path = tmp_path / "test_logs.jsonl"
    with file_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return file_path


#тествые записи для логов
@pytest.fixture
def sample_records():
    return [
        {
            "date": "2026-06-10 10:00:00",
            "server": "web01",
            "level": "ERROR",
            "message": "Database connection failed",
        },
        {
            "date": "2026-06-10 10:01:00",
            "server": "web01",
            "level": "INFO",
            "message": "Service started successfully",
        },
        {
            "date": "2026-06-10 10:02:00",
            "server": "web02",
            "level": "WARNING",
            "message": "High memory usage detected",
        },
        {
            "date": "2026-06-10 10:03:00",
            "server": "web02",
            "level": "WARNING",
            "message": "CPU load is above normal",
        },
        {
            "date": "2026-06-10 10:04:00",
            "server": "db01",
            "level": "ERROR",
            "message": "Backup job failed",
        },
    ]


def test_read_logs_success(tmp_path, sample_records):
    file_path = create_test_log_file(tmp_path, sample_records)
    analyzer = LogAnalyzer(str(file_path))

    logs = list(analyzer.read_logs())

    assert len(logs) == 5
    assert logs[0]["server"] == "web01"
    assert logs[0]["level"] == "ERROR"


def test_read_logs_file_not_found():
    analyzer = LogAnalyzer("missing_file.jsonl")

    with pytest.raises(FileNotFoundError):
        list(analyzer.read_logs())

#проверка, что дефдикт получил в нутрь еще 1
def test_build_structure(tmp_path, sample_records):
    file_path = create_test_log_file(tmp_path, sample_records)
    analyzer = LogAnalyzer(str(file_path))
    analyzer.build_structure()

    errors = analyzer.get_errors_for_server("web01")

    assert analyzer.records_count == 5
    assert errors == ["Database connection failed"]


def test_get_errors_for_server(tmp_path, sample_records):
    file_path = create_test_log_file(tmp_path, sample_records)
    analyzer = LogAnalyzer(str(file_path))

    analyzer.build_structure()

    assert analyzer.get_errors_for_server("web01") == ["Database connection failed"]
    assert analyzer.get_errors_for_server("web02") == []


def test_count_messages_by_level(tmp_path, sample_records):
    file_path = create_test_log_file(tmp_path, sample_records)
    analyzer = LogAnalyzer(str(file_path))

    analyzer.build_structure()

    result = analyzer.count_messages_by_level()

    assert result["web01"]["ERROR"] == 1
    assert result["web01"]["INFO"] == 1
    assert result["web01"]["WARNING"] == 0
    assert result["web02"]["WARNING"] == 2
    assert result["db01"]["ERROR"] == 1


def test_find_server_with_max_warnings(tmp_path, sample_records):
    file_path = create_test_log_file(tmp_path, sample_records)
    analyzer = LogAnalyzer(str(file_path))

    analyzer.build_structure()

    result = analyzer.find_server_with_max_warnings()

    assert result["server"] == "web02"
    assert result["warnings_count"] == 2


def test_add_log_creates_nested_structure():
    analyzer = LogAnalyzer("dummy.jsonl")
    analyzer.add_log(date="2026-06-10 12:00:00",  server="new-server01", level="ERROR", message="New error message")

    assert analyzer.get_errors_for_server("new-server01") == ["New error message"]
    assert analyzer.records_count == 1


def test_add_log_invalid_level():
    analyzer = LogAnalyzer("dummy.jsonl")
    with pytest.raises(ValueError):
        analyzer.add_log(date="2026-06-10 12:00:00",server="web01",level="CRITICAL", message="Invalid level message")


def test_export_report(tmp_path, sample_records):
    file_path = create_test_log_file(tmp_path, sample_records)
    report_path = tmp_path / "report.json"

    analyzer = LogAnalyzer(str(file_path))
    analyzer.build_structure()
    analyzer.create_report()
    analyzer.export_report(str(report_path))

    assert report_path.exists()
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["total_records"] == 5


def test_to_dict_and_from_dict(tmp_path, sample_records):
    file_path = create_test_log_file(tmp_path, sample_records)
    analyzer = LogAnalyzer(str(file_path))

    analyzer.build_structure()
    analyzer.create_report()

    data = analyzer.to_dict()
    restored = LogAnalyzer.from_dict(data)

    assert restored.file_path == str(file_path)
    assert restored.records_count == 5
    assert restored.get_errors_for_server("web01") == ["Database connection failed"]



def test_empty_file(tmp_path):
    file_path = tmp_path / "empty.jsonl"
    file_path.write_text("", encoding="utf-8")

    analyzer = LogAnalyzer(str(file_path))
    analyzer.build_structure()
    report = analyzer.create_report()

    assert analyzer.records_count == 0
    assert report["total_records"] == 0
    assert report["server_with_max_warnings"]["server"] is None
    assert report["server_with_max_warnings"]["warnings_count"] == 0