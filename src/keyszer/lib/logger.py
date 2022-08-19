VERBOSE = False


def debug(*args, ctx="DD"):
    if not VERBOSE:
        return

    # allow blank lines without context
    if len(args) == 0 or (len(args) == 1 and args[0] == ""):
        print("", flush=True)
        return
    print(f"({ctx})", *args, flush=True)


def warn(*args, ctx="WW"):
    print(f"({ctx})", *args, flush=True)


def error(*args, ctx="EE"):
    print(f"({ctx})", *args, flush=True)


def log(*args, ctx="--"):
    print(f"({ctx})", *args, flush=True)


def info(*args, ctx="--"):
    log(*args, ctx=ctx)
