#!/usr/bin/env python3
# chmod +x cope-pilot.py
# sudo cp ./cope-pilot.py /usr/local/bin/cope.py

import os
# import load_dotenv, find_dotenv
import click
import requests
import subprocess
from git import Repo
import openai

def load_gpt_token():
    return os.environ.get("GPT_TOKEN")

DEFAULT_PR_TEMPLATE = """
   ## Changes
   - change 1
   - change 2
   - change 3
   """

def generate_pr_comment(template, diffs):
    print(f"generating pull request comment from diffs: \n {diffs}")
    openai.api_key = load_gpt_token()
    prompt = f"you are an expert code reviewer you will take the code diffs and a PR template. You will use them to generate a short and concise description of the changes that goes into a Pull Request on GitHub. Firstly, here is a template: {template}. Now here are the git diffs: {diffs}. Now, generate the accompanying comments in markdown"
    messages = [{"role": "system", "content": prompt}]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=2048,
        n=1,
        temperature=0.5,
    )

    generated = response.choices[0].message.content
    return generated


def propose_command(description):
    openai.api_key = load_gpt_token()
    prompt = f"you are an expert in Linux, and the commandline. You are going to help a human developer accomplish the task he requires on the commandline. You will be given a description of the commandline task to be accomplished. You will provide a very short and concise description of the suggested command(s) that will accomplish the task. You will also provide the actual command. in its own line and code block in an easy way to copy. The following is the human's description of his intention: \n {description}. Now describe the command to run on the terminal and brief explaination"
    messages = [{"role": "system", "content": prompt}]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=2048,
        n=1,
        temperature=0.4,
    )

    generated = response.choices[0].message.content
    return generated


@click.group()
def cli():
    pass

# python3 cope-pilot.py gen-pr --repo ./ --source "master" --target "dev"
@cli.command()
@click.option("--repo", required=True, help="Path to the Git repository")
@click.option("--source", required=True, help="Source branch")
@click.option("--target", required=True, help="Target branch")
@click.option("--template", help="Pull request template")
def gen_pr(repo, source, target, template):
    repo_path = os.path.abspath(repo)
    repo = Repo(repo_path)
    diffs = repo.git.diff(f"{target}...{source}")

    if not template:
        template = DEFAULT_PR_TEMPLATE

    template = template.strip()

    pr_comment = generate_pr_comment(template, diffs)
    click.echo(pr_comment)


@cli.command()
@click.option("--description", prompt="Command description", help="Description of the command to generate")
def gen_cmd(description):
    cmd= propose_command(description)

    click.echo(cmd)
    # TODO: // use gpt4 function call to split up two outputs: the actual command and the comments for it
    # response = click.prompt("Accept the proposed command? (Y/N)", type=click.Choice(["Y", "N"]))

    # if response == "Y":
    #     subprocess.call(cmd, shell=True)
    #     click.echo("Command executed successfully!")
    # else:
    #     click.echo("Command rejected!")

def generate_context_string(language_key):
    prompt =  f"You are a helpful NLP code snippet generator, you will help a developer by creating a snippet in {language_key}. The code is expected to be clean, concise, readable, and highly reusable. You might receive a context in the form of source code in local development, or you might not. In the case that you may not, try your best to wrap the generated code in a function. The only non-code texts allowed are in the form of a language valid code comments. Make sure the response is in the form of a valid code that will run once intepreted or compiled, there should not be compilation error, syntax error, or logical error. Only use valid and legal code. Expect the entirety of the output to be generated as a source file with valid language extension \n YOU MUST NOT PUT IN LANGUAGE NAME NEXT TO THE CODE BLOCK '```', YOU MUST NOT USE CODE BLOCKS, '```', YOU MUST ALSO WRAP ALL text aside from code inside comment tags. For example this is a valid answer format in python: \n # Sure, Here is the answer to the question: \n [CODE ANSWER] \n"

    #  TODO add few shots examples for other languages
    fewshots = {
        'Python': """
        Q: how do you reverse a string in python in one line of code?
        A:
        # here is the code snippet to reverse a string in python
        # in one line of code
        ###
        ```
        my_string = "Hello World"[::-1]
        ```
        Q: how do you concat 2 strings in python?
        A:
        # Here's a one-liner code snippet to concatenate two strings in Python:
        # This code will concatenate the two strings "string1" and "string2" and store the result in the variable `new_string`. You can replace "string1" and "string2" with any strings you want to concatenate.
        ###

        ```
        new_string = "string1" + "string2"
        ```
        """,
        'JavaScript': """
        Q: how do you append a string in javascript in one line of code?
        A:
        // here is a line of code that reverse a string
        // This code defines an arrow function that takes a string as an argument, splits it into an array of characters, reverses the order of the elements in the array, and then joins the elements back into a string. The resulting string is returned as the output of the function.
        const reversedString = str => str.split('').reverse().join('');
        Q: how do you concat two strings in javascript?
        A:
        // here is a line of code that concatinate two strings
        const str = "hello".concat("world")
        ```,
        'Typescript': '',
        'Emacs Lisps': '',
        'Bash': '',
        'Linux Commands': '',
        """
    }

    return prompt + '\n' + fewshots.get(language_key.lower(), f"Few Shots example not available for language {language_key}")


def get_preloaded_context(language):
    language_contexts = {
        "js": generate_context_string("JavaScript"),
        "ts": generate_context_string("TypeScript"),
        "py": generate_context_string("Python"),
        "el": generate_context_string("Emacs Lisps"),
        "sh": generate_context_string("Bash"),
        "cmd": generate_context_string("Linux Commandline")+ " " + ". Expect the recommendation to work on a linux based distro such as Ubuntu and is safe, won't brick the machine or cost catastrophic damage to the systems",
    }

    return language_contexts.get(language.lower(), f"Unsupported language: {language}")

def extract_local_file_context(file_path):
    try:
        with open(file_path, "r") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        click.echo(f"File not found: {file_path}")
        return ""

def call_gpt3_api(task_description, language, local_file_context, preloaded_context):
    openai.api_key = load_gpt_token()

    messages = [{"role": "system", "content": preloaded_context}]
    if local_file_context:
        messages.append({"role": "user", "content": local_file_context})
    messages.append({"role": "user", "content": task_description})

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=2048,
        n=1,
        temperature=0.1,
    )

    generated_code = response.choices[0].message.content
    return generated_code

def save_code_snippet(code_snippet, output_file_path):
    with open(output_file_path, 'w') as file:
        file.write(code_snippet)

@cli.command()
@click.option('--language', type=click.Choice(['js', 'ts', 'py', 'el', 'sh', 'cmd'], case_sensitive=False), prompt='select a language extension',help='The programming language for the code snippet.')
@click.option('--task', prompt='Enter a task description', help='The task description in natural language.')
@click.option('--file-path', default=None, help='The path to a local file for context (optional).')
@click.option('--output', default=None, help='The output file name and location (optional).')
def gen_code(language, task, file_path, output):
    gpt_token = load_gpt_token()
    if not gpt_token:
        click.echo("GPT_TOKEN environment variable not found. Please set it and try again.")
        return

    preloaded_context = get_preloaded_context(language)
    local_file_context = ''

    if file_path:
        local_file_context = extract_local_file_context(file_path)

    gpt3_response = call_gpt3_api(task, language, local_file_context, preloaded_context)

    if output:
        save_code_snippet(gpt3_response, output)
        click.echo(f"Generated code snippet saved to: {output}")
    else:
        click.echo(gpt3_response)


if __name__ == "__main__":
    print('running cope pilot')
    cli()
