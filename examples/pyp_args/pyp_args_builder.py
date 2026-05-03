"""
PYP Args Builder Demo

This example creates a target module and a runner module, then executes the runner.
It demonstrates USEKIT PYP function execution with positional arguments,
keyword arguments, list arguments, and flexible *args/**kwargs.
"""

from usekit import use, uw


use.write.pyp.base(r'''"""
PYP Args Demo Target Module

This module defines normal Python functions that can be executed through USEKIT:

    use.exec.pyp.base("examples.pyp_args_demo:add", 10, 20)
"""

from usekit import uw


def add(a, b):
    """Return a + b."""
    result = a + b
    uw.p(f"[ADD] {a} + {b} = {result}")
    return result


def multiply(x, y, z=1):
    """Return x * y * z."""
    result = x * y * z
    uw.p(f"[MULTIPLY] {x} * {y} * {z} = {result}")
    return result


def greet(name, title="Mr.", greeting="Hello"):
    """Return a greeting message."""
    message = f"{greeting}, {title} {name}!"
    uw.p(f"[GREET] {message}")
    return message


def process_list(items, operation="sum"):
    """Process a list with sum, product, or avg."""
    uw.p(f"[PROCESS] Operation: {operation}")
    uw.p(f"[PROCESS] Items: {items}")

    if operation == "sum":
        result = sum(items)
    elif operation == "product":
        result = 1
        for item in items:
            result *= item
    elif operation == "avg":
        result = sum(items) / len(items)
    else:
        result = items

    uw.p(f"[PROCESS] Result: {result}")
    return result


def complex_calc(a, b, c, operation="+", verbose=False):
    """Run a calculation with multiple operation modes."""
    if verbose:
        uw.p(f"[CALC] Starting: a={a}, b={b}, c={c}, operation={operation}")

    if operation == "+":
        result = a + b + c
    elif operation == "*":
        result = a * b * c
    elif operation == "mixed":
        result = (a + b) * c
    else:
        result = a

    if verbose:
        uw.p(f"[CALC] Result: {result}")

    return result


def show_info(*args, **kwargs):
    """Return information about positional and keyword arguments."""
    uw.p(f"[INFO] Positional args: {args}")
    uw.p(f"[INFO] Keyword args: {kwargs}")

    return {
        "args": args,
        "kwargs": kwargs,
        "total_args": len(args),
        "total_kwargs": len(kwargs),
    }


if __name__ == "__main__":
    uw.p("PYP Args Demo Target Module")
    uw.p("Run this module with use.exec.pyp.base() from pyp_args_runner.py")
''', "pyp_args_demo", "examples")


use.write.pyp.base(r'''"""
PYP Args Runner Demo

This example shows how to execute functions from another PYP module
with positional arguments, keyword arguments, lists, and *args/**kwargs.
"""

from usekit import use, uw


def main():
    uw.p("=" * 60)
    uw.p("PYP Args Runner Demo")
    uw.p("=" * 60)

    result = use.exec.pyp.base("examples.pyp_args_demo:add", 10, 20)
    uw.p(f"Returned: {result}")

    result = use.exec.pyp.base("examples.pyp_args_demo:multiply", 2, 3, z=4)
    uw.p(f"Returned: {result}")

    result = use.exec.pyp.base(
        "examples.pyp_args_demo:greet",
        "Alice",
        title="Dr.",
        greeting="Welcome",
    )
    uw.p(f"Returned: {result}")

    result = use.exec.pyp.base(
        "examples.pyp_args_demo:process_list",
        [1, 2, 3, 4, 5],
        operation="avg",
    )
    uw.p(f"Returned: {result}")

    result = use.exec.pyp.base(
        "examples.pyp_args_demo:complex_calc",
        2,
        3,
        4,
        operation="mixed",
        verbose=True,
    )
    uw.p(f"Returned: {result}")

    result = use.exec.pyp.base(
        "examples.pyp_args_demo:show_info",
        1,
        2,
        3,
        mode="debug",
        active=True,
    )
    uw.p(f"Returned: {result}")

    uw.ok("PYP args runner completed")


if __name__ == "__main__":
    main()
''', "pyp_args_runner", "examples")


uw.ok("PYP args demo files created")

use.exec.pyp.base("examples.pyp_args_runner")
