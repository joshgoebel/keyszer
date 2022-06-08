def debug(*args, ctx = "DD"):
    print(f"({ctx})", *args)


def warn(*args, ctx = "WW"):
    print(f"({ctx})", *args)


def error(*args, ctx = "EE"):
    print(f"({ctx})", *args)


def log(*args, ctx = "--"):
    print(f"({ctx})", *args)


def info(*args, ctx = "--"):
    log(*args, ctx = ctx)