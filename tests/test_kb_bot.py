from src.kb_bot import DeadlineRequest


def test_request_keeps_course_context():
    request = DeadlineRequest("Mina", "biology", "When is the lab due?")
    assert request.course == "biology"
    assert request.learner == "Mina"
