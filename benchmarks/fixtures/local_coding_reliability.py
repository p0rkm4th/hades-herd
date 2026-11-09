"""Deterministic, small local Codex coding tasks and independent validators."""

TASKS = {
    "smoke": {
        "prompt": "Implement `greet(name)` in greeting.py so it returns `Hello, NAME!` with surrounding whitespace stripped from NAME. Run pytest. Change only greeting.py; finish with a brief result.",
        "files": {
            "greeting.py": "\"\"\"Greeting helpers.\"\"\"\n",
            "tests/test_greeting.py": "from greeting import greet\n\ndef test_greeting():\n    assert greet('Ada') == 'Hello, Ada!'\n    assert greet('  Lin  ') == 'Hello, Lin!'\n",
        },
        "verify": "from greeting import greet\nassert greet('Ada') == 'Hello, Ada!'\nassert greet('  Lin  ') == 'Hello, Lin!'\n",
        "allowed": ["greeting.py"],
    },
    "bug_fix": {
        "prompt": "Fix `charge_amount` in billing.py to reject negative/non-integer cents and tax rates outside integer 0..100 with ValueError. Preserve integer-cent arithmetic. Run pytest. Change only billing.py; finish with a brief result.",
        "files": {
            "billing.py": "def charge_amount(subtotal_cents, tax_percent):\n    return subtotal_cents + subtotal_cents * tax_percent // 100\n",
            "tests/test_billing.py": "import pytest\nfrom billing import charge_amount\n\ndef test_tax():\n    assert charge_amount(1000, 8) == 1080\n    assert charge_amount(101, 0) == 101\n\n@pytest.mark.parametrize('cents,rate', [(-1, 5), (10, -1), (10, 101), (True, 5), (10, 2.5)])\ndef test_invalid(cents, rate):\n    with pytest.raises(ValueError):\n        charge_amount(cents, rate)\n",
        },
        "verify": "import pytest\nfrom billing import charge_amount\nassert charge_amount(1000, 8) == 1080\nassert charge_amount(101, 0) == 101\nfor args in [(-1, 5), (10, -1), (10, 101), (True, 5), (10, 2.5)]:\n    with pytest.raises(ValueError): charge_amount(*args)\n",
        "allowed": ["billing.py"],
    },
    "feature": {
        "prompt": "Implement `slugify_label(text)` in labels.py. Apply Unicode NFKD normalization, drop combining marks, lowercase, replace each run of non-ASCII-alphanumeric characters with one hyphen, and trim hyphens. Run pytest. Change only labels.py; finish with a brief result.",
        "files": {
            "labels.py": "\"\"\"Human label helpers.\"\"\"\n",
            "tests/test_labels.py": "from labels import slugify_label\n\ndef test_slugify():\n    assert slugify_label('  Crème brûlée / Menu  ') == 'creme-brulee-menu'\n    assert slugify_label('A__B---C') == 'a-b-c'\n    assert slugify_label('') == ''\n",
        },
        "verify": "from labels import slugify_label\nassert slugify_label('  Crème brûlée / Menu  ') == 'creme-brulee-menu'\nassert slugify_label('A__B---C') == 'a-b-c'\nassert slugify_label('') == ''\n",
        "allowed": ["labels.py"],
    },
    "refactor": {
        "prompt": "Refactor duration.py without changing behavior: extract a pure `split_duration(total_seconds)` helper returning `(hours, minutes, seconds)` with all values nonnegative; make `format_duration` use it. Keep the public formatter unchanged. Run pytest. Change only duration.py; finish with a brief result.",
        "files": {
            "duration.py": "def format_duration(total_seconds):\n    if not isinstance(total_seconds, int) or isinstance(total_seconds, bool):\n        raise TypeError('seconds must be an integer')\n    if total_seconds < 0:\n        raise ValueError('seconds must be nonnegative')\n    if total_seconds < 60:\n        return f'0:00:{total_seconds:02d}'\n    if total_seconds < 3600:\n        minutes = total_seconds // 60\n        seconds = total_seconds - minutes * 60\n        return f'0:{minutes:02d}:{seconds:02d}'\n    hours = total_seconds // 3600\n    minutes = (total_seconds - hours * 3600) // 60\n    seconds = total_seconds - hours * 3600 - minutes * 60\n    return f'{hours}:{minutes:02d}:{seconds:02d}'\n",
            "tests/test_duration.py": "import pytest\nfrom duration import format_duration\n\ndef test_public_behavior():\n    assert format_duration(0) == '0:00:00'\n    assert format_duration(59) == '0:00:59'\n    assert format_duration(3600) == '1:00:00'\n    assert format_duration(90061) == '25:01:01'\n    with pytest.raises(ValueError): format_duration(-1)\n    with pytest.raises(TypeError): format_duration(1.5)\n",
        },
        "verify": "import inspect, pytest, duration\nassert callable(getattr(duration, 'split_duration', None))\nassert duration.split_duration(90061) == (25, 1, 1)\nassert duration.split_duration(59) == (0, 0, 59)\nassert duration.format_duration(0) == '0:00:00'\nassert duration.format_duration(90061) == '25:01:01'\nwith pytest.raises(ValueError): duration.split_duration(-1)\nwith pytest.raises(TypeError): duration.split_duration(1.5)\nassert 'split_duration(' in inspect.getsource(duration.format_duration)\n",
        "allowed": ["duration.py"],
    },
    "multi_file": {
        "prompt": "Add JSON output support to this settings CLI. Add `--json` to cli.py; when given, print the loaded settings as sorted, indented JSON, otherwise preserve the existing `key=value` output. Update settings.py/cli.py only as needed and add tests in tests/test_cli.py. Run pytest. Do not change unrelated files; finish with a brief result.",
        "files": {
            "settings.py": "def load_settings(text):\n    result = {}\n    for line in text.splitlines():\n        line = line.strip()\n        if line and not line.startswith('#') and '=' in line:\n            key, value = line.split('=', 1)\n            result[key.strip()] = value.strip()\n    return result\n",
            "cli.py": "import sys\nfrom settings import load_settings\n\ndef main(argv=None):\n    argv = list(sys.argv[1:] if argv is None else argv)\n    text = argv[0] if argv else ''\n    settings = load_settings(text)\n    for key in sorted(settings):\n        print(f'{key}={settings[key]}')\n    return 0\n\nif __name__ == '__main__':\n    raise SystemExit(main())\n",
            "tests/test_cli.py": "from cli import main\n\ndef test_default_output(capsys):\n    assert main(['b=2\\na=1']) == 0\n    assert capsys.readouterr().out == 'a=1\\nb=2\\n'\n",
        },
        "verify": "import contextlib, io, json, cli\nout=io.StringIO()\nwith contextlib.redirect_stdout(out): assert cli.main(['--json', 'b=2\\na=1']) == 0\nassert json.loads(out.getvalue()) == {'a':'1','b':'2'}\nout=io.StringIO()\nwith contextlib.redirect_stdout(out): assert cli.main(['b=2\\na=1']) == 0\nassert out.getvalue() == 'a=1\\nb=2\\n'\n",
        "allowed": ["cli.py", "settings.py", "tests/test_cli.py"],
    },
    "debugging": {
        "prompt": "Diagnose the retry-delay defect using retry.log and test_retry.py. Fix retry_delay so delays grow exponentially but never exceed max_delay. Run pytest. Change only retry.py; finish with a brief result.",
        "files": {
            "retry.py": "def retry_delay(attempt, base_delay=1, max_delay=8):\n    if attempt < 0:\n        raise ValueError('attempt must be nonnegative')\n    return min(base_delay, max_delay) * (2 ** attempt)\n",
            "retry.log": "attempt=0 delay=1\nattempt=1 delay=2\nattempt=2 delay=4\nattempt=3 delay=8\nattempt=4 delay=16\nexpected: delay must stay at or below 8 seconds\n",
            "tests/test_retry.py": "import pytest\nfrom retry import retry_delay\n\ndef test_growth_and_cap():\n    assert [retry_delay(i) for i in range(5)] == [1, 2, 4, 8, 8]\n\ndef test_invalid_attempt():\n    with pytest.raises(ValueError): retry_delay(-1)\n",
        },
        "verify": "import pytest\nfrom retry import retry_delay\nassert [retry_delay(i) for i in range(5)] == [1,2,4,8,8]\nwith pytest.raises(ValueError): retry_delay(-1)\n",
        "allowed": ["retry.py"],
    },
}

FULL_TASKS = ("bug_fix", "feature", "refactor", "multi_file", "debugging")
