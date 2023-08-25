# Sure, here is a refactored version of the code with smaller functions:

# ```python
#!/usr/bin/env python3

import os
import click
import openai


def load_gpt_token():
    return os.environ.get("GPT_TOKEN")


def generate_context_string(language_key):
    return f"You are a helpful NLP code snippet generator, you will help a developer by creating a snippet in {language_key}. The code is expected to be clean, concise, readable, and highly reusable. You might receive a context in the form of source code in local development, or you might not. In the case that you may not, try your best to wrap the generated code in a function. The only non-code texts allowed are in"
