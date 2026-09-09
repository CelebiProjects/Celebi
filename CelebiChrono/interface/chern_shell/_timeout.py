"""Parse the shared HTTP timeout option for interactive commands."""
import shlex


def parse_timeout(arg):
    """Return remaining arguments and an optional positive timeout keyword."""
    args = shlex.split(arg)
    remaining = []
    options = {}
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--":
            remaining.extend(args[index:])
            break
        if token == "--timeout" or token.startswith("--timeout="):
            if token == "--timeout":
                index += 1
                if index == len(args):
                    raise ValueError("--timeout requires a positive integer in seconds")
                value = args[index]
            else:
                value = token.split("=", 1)[1]
            try:
                timeout = int(value)
            except ValueError as exc:
                raise ValueError("--timeout requires a positive integer in seconds") from exc
            if timeout < 1:
                raise ValueError("--timeout requires a positive integer in seconds")
            options["timeout"] = timeout
        else:
            remaining.append(token)
        index += 1
    return remaining, options
