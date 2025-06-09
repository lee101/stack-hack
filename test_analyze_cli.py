import subprocess


def test_cli_help():
    result = subprocess.run(["python", "analyze_cli.py", "-h"], capture_output=True, text=True)
    assert "usage" in result.stdout
