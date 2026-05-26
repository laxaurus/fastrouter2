#!/usr/bin/env python3
"""Generate a LiteLLM config.yaml from environment variables."""
import os
import sys

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "config.template.yaml")


def generate():
    with open(TEMPLATE_PATH) as f:
        template = f.read()

    config = template.replace("os.environ/DEEPSEEK_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))
    config = config.replace("os.environ/QWEN_API_KEY", os.environ.get("QWEN_API_KEY", ""))
    config = config.replace("os.environ/LITELLM_MASTER_KEY", os.environ.get("LITELLM_MASTER_KEY", "sk-master-key"))

    output_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(output_path, "w") as f:
        f.write(config)

    print(f"Generated {output_path}")


if __name__ == "__main__":
    generate()
