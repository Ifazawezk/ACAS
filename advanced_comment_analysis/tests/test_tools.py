"""Scripts in tools/ that call the API have to log in, because nearly every route needs a token."""
import re
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
CALLS_THE_API = re.compile(r"requests\.(get|post|put|delete|request)\(|urlopen\(|TestClient\(")


def test_tools_that_call_the_api_send_a_token():
    without_token = []
    for path in sorted(TOOLS.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if CALLS_THE_API.search(text) and "Authorization" not in text:
            without_token.append(path.name)
    assert without_token == []
