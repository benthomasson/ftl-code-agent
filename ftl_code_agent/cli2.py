#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
from ftl_code_agent.core import create_model, run_agent
from ftl_code_agent.util import get_functions
from ftl_code_agent.default_tools import TOOLS
from ftl_code_agent.tools import get_tool, load_code
from ftl_code_agent.codegen import (
    generate_python_header,
    reformat_python,
    generate_python_tool_call,
    generate_explain_header,
    generate_explain_action_step,
)
from ftl_code_agent.memory import ActionStep
from smolagents.agent_types import AgentText


def generate_test(model, code_files, tools, prompt, output, explain):

    tool_classes = {}
    tool_classes.update(TOOLS)
    for cf in code_files:
        tool_classes.update(load_code(cf))
    model = create_model(model)
    state = {
    }

    generate_python_header(
        output,
        prompt,
        [],
        code_files,
        tools,
    )
    generate_explain_header(explain, prompt)

    for o in run_agent(
        tools=[get_tool(tool_classes, t, state) for t in tools],
        model=model,
        problem_statement=prompt,
    ):
        if isinstance(o, ActionStep):
            generate_explain_action_step(explain, o)
            if o.trace and o.tool_calls:
                for call in o.tool_calls:
                    generate_python_tool_call(output, call)
        elif isinstance(o, AgentText):
            print(o.to_string())

    reformat_python(output)


@click.command()
@click.argument("code-file")
@click.option("--model", "-m", default="ollama_chat/deepseek-r1:14b")
def main(model, code_file):
    print(code_file)
    module, fns = get_functions(code_file)
    print(module.__name__, [fn.__name__ for fn in fns])

    for fn in fns:
        fn_name = fn.__name__
        tools = ['complete', fn_name]
        prompt = f"Call {fn_name} with suitable arguments, use assert statement on the result to make sure it is correct, and then complete."
        output = f"test_{fn_name}.py"
        explain = f"test_{fn_name}.txt"
        generate_test(model, [code_file], tools, prompt, output, explain)


if __name__ == "__main__":
    main()
