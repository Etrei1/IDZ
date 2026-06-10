from src.analyz import LogAnalyzer

def main():
    analyzer = LogAnalyzer("../data/logs.jsonl")

    analyzer.build_structure()

    print("ERROR-сообщения для web01:")
    for message in analyzer.get_errors_for_server("web01"):
        print("-", message)

    print("\nКоличество сообщений по серверам:")
    print(analyzer.count_messages_by_level())

    print("\nСервер с максимальным количеством WARNING:")
    print(analyzer.find_server_with_max_warnings())

    analyzer.add_log(
        date="2026-06-10 15:30:00",
        server="new-server01",
        level="ERROR",
        message="New test error message",
    )

    print("\nERROR-сообщения для new-server01:")
    print(analyzer.get_errors_for_server("new-server01"))

    analyzer.create_report()
    analyzer.export_report("reports/report.json")
    analyzer.save_state("state/analyzer_state.json")

    print("\nОтчёт сохранён в reports/report.json")
    print("Состояние сохранено в state/analyzer_state.json")


if __name__ == "__main__":
    main()