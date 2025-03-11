#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
from ftl_code_agent.core import create_model, run_agent
from ftl_code_agent.util import get_functions, get_function_code
from ftl_code_agent.default_tools import TOOLS
from ftl_code_agent.tools import get_tool
from ftl_code_agent.codegen import (
    reformat_python,
    generate_explain_header,
    generate_explain_action_step,
)
from ftl_code_agent.memory import ActionStep
from smolagents.agent_types import AgentText

from redbaron import RedBaron
import shutil


def generate_code(model, code_file, function, output, explain):

    print(f"{code_file=} {function=} {output=} {explain=}")

    tool_classes = {}
    tool_classes.update(TOOLS)
    model = create_model(model)
    state = {
        "func": None,
    }

    tools = ["complete"]

    module, fns = get_functions(code_file)

    fn = state["func"] = getattr(module, function)
    function_code = get_function_code(fn)

    prompt = f"""Given the following python function signature and docstring write the code
    that implements the docstring.  Then call complete().

The function:
{function_code}

    """

    # print(prompt)

    generate_explain_header(explain, prompt)

    code_blocks = []

    for o in run_agent(
        tools=[get_tool(tool_classes, t, state) for t in tools],
        model=model,
        problem_statement=prompt,
    ):
        if isinstance(o, ActionStep):
            generate_explain_action_step(explain, o)
            if o.trace and o.tool_calls:
                for call in o.tool_calls:
                    code_blocks.append(call.arguments)
        elif isinstance(o, AgentText):
            print(o.to_string())

    # print(code_blocks)
    with open(code_file) as f:
        red = RedBaron(f.read())

    target = None
    for o in red:
        if o.name == function and o.type == "def":
            target = o
            break

    if target is None:
        raise Exception(f"function {function} not found in code")

    found = False
    for code_block in code_blocks:
        # print(code_block)
        red_fn = RedBaron(code_block)
        # red_fn.help()
        for o in red_fn:
            if o.name == function and o.type == "def":
                target.replace(o)
                found = True
                break
        else:
            continue
        break

    if found is None:
        raise Exception(f"function {function} not found in code blocks")

    # red = RedBaron(function_code)
    # pprint(red.dumps())
    # print(json.dumps(red.fst(), indent=4))
    # red.help()
    # print(state['docstring'])
    # red[0].value.insert(0, f'\n"""{state["docstring"]}"""\n')
    # pprint(red.dumps())

    with open(output, "w") as f:
        f.write(red.dumps())

    reformat_python(output)
    pass


@click.command()
@click.argument("code-file")
@click.option("--model", "-m", default="ollama_chat/deepseek-r1:14b")
@click.option("--output", "-o", default="output.py")
def main(model, code_file, output):
    print(code_file)
    module, fns = get_functions(code_file)
    print(module.__name__, [fn.__name__ for fn in fns])

    if code_file != output:
        shutil.copy(code_file, output)

    for fn in fns:
        fn_name = fn.__name__
        explain = f"{fn_name}.txt"
        generate_code(model, output, fn_name, output, explain)


if __name__ == "__main__":
    main()
