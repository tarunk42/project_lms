from src.example import print_message

def test_example(capfd):
    print_message()
    captured = capfd.readouterr()
    assert captured.out.strip() == "Hello, this is a message from example.py!"