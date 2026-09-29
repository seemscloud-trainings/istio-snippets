"""Shared YAML formatting: singleton sequences use brackets, including object lists."""

import yaml


class SnippetDumper(yaml.SafeDumper):
    def represent_sequence(self, tag, sequence, flow_style=None):
        return super().represent_sequence(tag, sequence, flow_style=len(sequence) == 1)


def represent_string(dumper, value):
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|" if "\n" in value else None)


SnippetDumper.add_representer(str, represent_string)


def dump_documents(documents):
    return yaml.dump_all(
        documents, Dumper=SnippetDumper, sort_keys=False,
        allow_unicode=True, width=10000, default_flow_style=False,
    )
