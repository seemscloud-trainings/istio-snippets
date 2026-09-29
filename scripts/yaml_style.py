"""Shared YAML formatting: singleton sequences use brackets, including object lists."""

import yaml


class SnippetDumper(yaml.SafeDumper):
    def represent_sequence(self, tag, sequence, flow_style=None):
        return super().represent_sequence(tag, sequence, flow_style=len(sequence) == 1)


def dump_documents(documents):
    return yaml.dump_all(
        documents, Dumper=SnippetDumper, sort_keys=False,
        allow_unicode=True, width=10000, default_flow_style=False,
    )
