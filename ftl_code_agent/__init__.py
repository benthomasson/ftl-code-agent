from contextlib import contextmanager

from smolagents.tools import Tool
from .tools import load_tools, get_tool, load_code
from .default_tools import TOOLS
from dataclasses import dataclass
from ftl_doc_agent.local_python_executor import FinalAnswerException


class Tools(object):
    def __init__(self, tools: dict[str, Tool]):
        self.__dict__.update(tools)


@dataclass
class FTL:
    tools: Tools


@contextmanager
def fixtures(tools_files, code_files, tools, **kwargs):
    tool_classes = {}
    tool_classes.update(TOOLS)
    state = {
    }
    state.update(kwargs)
    for tf in tools_files:
        tool_classes.update(load_tools(tf))
    for cf in code_files:
        tool_classes.update(load_code(cf))
    ftl = FTL(
        tools=Tools({name: get_tool(tool_classes, name, state) for name in tools})
    )
    try:
        yield ftl
    except FinalAnswerException as e:
        print(e)
