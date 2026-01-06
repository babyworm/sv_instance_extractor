import re
from typing import List, Tuple


class SVParser:
    MODULE_DEF_PATTERN = re.compile(r"^\s*module\s+(\w+)", re.MULTILINE)
    PACKAGE_DEF_PATTERN = re.compile(r"^\s*package\s+(\w+)", re.MULTILINE)
    INSTANCE_PATTERN = re.compile(
        r"^\s*(\w+)\s+"
        r"(?:#\s*\((?:[^()]*|\([^()]*\))*\)\s*)?"
        r"(\w+)\s*\(",
        re.MULTILINE | re.DOTALL,
    )

    SV_KEYWORDS = frozenset(
        [
            "if",
            "for",
            "case",
            "while",
            "begin",
            "end",
            "initial",
            "always",
            "always_comb",
            "always_ff",
            "module",
            "package",
            "interface",
            "function",
            "task",
            "property",
            "sequence",
            "covergroup",
            "class",
        ]
    )

    @staticmethod
    def find_modules(content: str) -> List[str]:
        return SVParser.MODULE_DEF_PATTERN.findall(content)

    @staticmethod
    def find_packages(content: str) -> List[str]:
        return SVParser.PACKAGE_DEF_PATTERN.findall(content)

    @staticmethod
    def find_instances(content: str) -> List[Tuple[str, str]]:
        instances = []
        for match in SVParser.INSTANCE_PATTERN.finditer(content):
            module_type = match.group(1)
            instance_name = match.group(2)
            if module_type not in SVParser.SV_KEYWORDS:
                instances.append((module_type, instance_name))
        return instances

    @staticmethod
    def replace_module_name(content: str, old_name: str, new_name: str) -> str:
        module_pattern = re.compile(r"(\bmodule\s+)" + re.escape(old_name) + r"(\b)")
        endmodule_pattern = re.compile(
            r"(endmodule\s*:?\s*)" + re.escape(old_name) + r"\b"
        )

        content = module_pattern.sub(r"\1" + new_name + r"\2", content)
        content = endmodule_pattern.sub(lambda m: m.group(1) + new_name, content)
        return content

    @staticmethod
    def replace_instance_type(
        content: str, old_type: str, new_type: str
    ) -> Tuple[str, List[int]]:
        lines = content.split("\n")
        modified_lines = []
        pattern = re.compile(r"\b" + re.escape(old_type) + r"\b")

        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                modified_lines.append(i)
                lines[i - 1] = pattern.sub(new_type, line)

        return "\n".join(lines), modified_lines
