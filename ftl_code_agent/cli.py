import click

from .core import create_model, run_agent
from .default_tools import TOOLS
from .tools import get_tool
from .codegen import (
    generate_explain_header,
    generate_explain_action_step,
    reformat_python,
)
from ftl_doc_agent.memory import ActionStep
from smolagents.agent_types import AgentText
from .util import get_functions, get_function_code
import json

from redbaron import RedBaron

from pprint import pprint



@click.command()
@click.argument("code-file")
@click.argument("function")
@click.option("--model", "-m", default="ollama_chat/deepseek-r1:14b")
@click.option("--output", "-o", default="output.py")
@click.option("--explain", "-e", default="output.txt")
def main(
    code_file,
    function,
    model,
    output,
    explain,
):
    """An agent that updates code with docstrings"""

    tool_classes = {}
    tool_classes.update(TOOLS)
    model = create_model(model)
    state = {
        'docstring': '',
        'func': None,
    }

    tools = ['docstring', 'complete']

    module, fns = get_functions(code_file)

    fn = state['func'] = getattr(module, function)
    function_code = get_function_code(fn)

    prompt = f"""Given the defintion the following python function create a docstring that explains what the function does,
what the arguments are, and what the function returns.  Update the code with new docstring using docstring() .
Finally call complete when done.   Do not define the function again.  Use the Google-style docstring using 'Args:' and 'Returns:' like
this:

    Parses a Google-style docstring to extract the function description,
    argument descriptions, and return description.

    Args:
        docstring: The docstring to parse.

    Returns:
        The function description, arguments, and return description.

The function:
{function_code}

    """

    print(prompt)

    generate_explain_header(explain, prompt)

    for o in run_agent(
        tools=[get_tool(tool_classes, t, state) for t in tools],
        model=model,
        problem_statement=prompt,
    ):
        if isinstance(o, ActionStep):
            generate_explain_action_step(explain, o)
        elif isinstance(o, AgentText):
            print(o.to_string())

    red = RedBaron(function_code)
    pprint(red.dumps())
    print(json.dumps(red.fst(), indent=4))
    red.help()
    print(state['docstring'])
    red[0].value.insert(0, f'\n"""{state["docstring"]}"""\n')
    pprint(red.dumps())

    with open(output, 'w') as f:
        f.write(red.dumps())
        print(red.dumps())


    reformat_python(output)
