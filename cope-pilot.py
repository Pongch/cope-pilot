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


if __name__ == "__main__":
    print('running cope pilot')
    cli()
