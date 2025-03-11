from smolagents.tools import Tool
from ftl_code_agent.tools import get_json_schema
from ftl_code_agent.local_python_executor import FinalAnswerException
from ftl_code_agent.tools import _convert_type_hints_to_json_schema

import re
import json

from smolagents._function_type_hints_utils import (
    _parse_google_format_docstring,
    DocstringParsingException,
)


class Complete(Tool):
    name = "complete"

    def __init__(self, state, *args, **kwargs):
        self.state = state
        super().__init__(*args, **kwargs)

    def forward(self, message: str = "Task was completed"):
        """
        Mark the solution as complete.

        Args:
            message: A completion message
        """

        raise FinalAnswerException(message)

    description, inputs, output_type = get_json_schema(forward)


class Impossible(Tool):
    name = "impossible"

    def __init__(self, state, *args, **kwargs):
        self.state = state
        super().__init__(*args, **kwargs)

    def forward(self, message: str = "Task was impossible"):
        """
        Mark the solution as impossible

        Args:
            message: A message explaining why the task was impossible
        """

        raise FinalAnswerException(message)

    description, inputs, output_type = get_json_schema(forward)


class DocString(Tool):
    name = "docstring"

    def __init__(self, state, *args, **kwargs):
        self.state = state
        super().__init__(*args, **kwargs)

    def forward(self, docstring: str, function: str = None):
        """
        Update the docstring for the function.

        Args:
            docstring: A string containing the docstring for the function.
            function: the name of the function.
        """

        func = self.state["func"]
        main_doc, param_descriptions, return_doc = _parse_google_format_docstring(
            docstring
        )
        json_schema = _convert_type_hints_to_json_schema(func)
        if (return_dict := json_schema["properties"].pop("return", None)) is not None:
            if (
                return_doc is not None
            ):  # We allow a missing return docstring since most templates ignore it
                return_dict["description"] = return_doc
        else:
            return_dict = {}
        for arg, schema in json_schema["properties"].items():
            if "arg" == "self":
                continue
            if arg not in param_descriptions:
                raise DocstringParsingException(
                    f"Cannot generate JSON schema for {func.__name__} because the docstring has no description for the argument '{arg}'"
                )
            desc = param_descriptions[arg]
            enum_choices = re.search(
                r"\(choices:\s*(.*?)\)\s*$", desc, flags=re.IGNORECASE
            )
            if enum_choices:
                schema["enum"] = [c.strip() for c in json.loads(enum_choices.group(1))]
                desc = enum_choices.string[: enum_choices.start()].strip()
            schema["description"] = desc

        self.state["docstring"] = docstring

    description, inputs, output_type = get_json_schema(forward)


TOOLS = {
    "complete": Complete,
    "impossible": Impossible,
    "docstring": DocString,
}
