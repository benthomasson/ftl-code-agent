import click

from .core import create_model, make_agent
from .default_tools import TOOLS
from .tools import get_tool, load_tools, load_code
import gradio as gr
from functools import partial

from .codegen import (
    generate_python_header,
    reformat_python,
    generate_explain_header,
)

from ftl_doc_agent.util import Bunch
from ftl_doc_agent.Gradio_UI import stream_to_gradio


def bot(context, prompt, messages, tools):
    agent = make_agent(
        tools=[get_tool(context.tool_classes, t, context.state) for t in tools],
        model=context.model,
    )
    generate_python_header(
        context.python,
        prompt,
        context.tools_files,
        context.code_files,
        tools,
    )
    generate_explain_header(context.explain, prompt)

    def update_code():
        nonlocal python_output
        with open(context.python) as f:
            python_output = f.read()

    python_output = ""

    update_code()

    # chat interface only needs the latest messages yielded
    messages = []
    messages.append(gr.ChatMessage(role="user", content=prompt))
    yield messages, python_output
    for msg in stream_to_gradio(
        agent, context, task=prompt, reset_agent_memory=False
    ):
        update_code()
        messages.append(msg)
        yield messages, python_output

    reformat_python(context.python)
    update_code()
    yield messages, python_output


def launch(context, tool_classes, **kwargs):
    with gr.Blocks(fill_height=True) as demo:
        python_code = gr.Code(render=False)
        with gr.Row():
            with gr.Column():
                chatbot = gr.Chatbot(
                    label="Agent",
                    type="messages",
                    resizeable=True,
                    scale=1,
                )
                gr.ChatInterface(
                    fn=partial(bot, context),
                    type="messages",
                    chatbot=chatbot,
                    additional_inputs=[
                        gr.CheckboxGroup(
                            choices=sorted(tool_classes), label="Tools"
                        ),
                    ],
                    additional_outputs=[python_code],
                )

            with gr.Column():
                python_code.render()

        demo.launch(debug=True, **kwargs)


@click.command()
@click.option("--code-files", "-c", multiple=True)
@click.option("--tools-files", "-f", multiple=True)
@click.option("--tools", "-t", multiple=True)
@click.option("--model", "-m", default="ollama_chat/deepseek-r1:14b")
@click.option("--python", "-o", default="output.py")
@click.option("--explain", "-o", default="output.txt")
def main(
    code_files,
    tools_files,
    tools,
    model,
    python,
    explain,
):
    """A agent that solves a problem given a system design and a set of tools"""
    tool_classes = {}
    tool_classes.update(TOOLS)
    for tf in tools_files:
        tool_classes.update(load_tools(tf))
    for cf in code_files:
        tool_classes.update(load_code(cf))
    print(f"{tool_classes=}")
    model = create_model(model)
    state = {
    }

    context = Bunch(
        tool_classes=tool_classes,
        tools_files=tools_files,
        code_files=code_files,
        tools=tools,
        model=model,
        python=python,
        explain=explain,
        state=state,
    )

    launch(context, tool_classes)
