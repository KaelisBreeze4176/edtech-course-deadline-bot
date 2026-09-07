from src.kb_bot import DeadlineRequest, KnowledgeBase


def main() -> None:
    kb = KnowledgeBase()
    kb.prepare()
    kb.add_note("math-week-2", "Algebra assignment is due Friday 17:00.", {"course": "algebra", "deadline": "Friday 17:00"})
    print(kb.answer(DeadlineRequest("Ari", "algebra", "When is my assignment due?")))


if __name__ == "__main__":
    main()
