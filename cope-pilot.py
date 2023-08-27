import os
import click
import requests
import subprocess
from git import Repo

GPT4_API_URL = "https://api.gpt4-api.com"
DEFAULT_PR_TEMPLATE = """
## Pull Request

Please review the following changes:

{diffs}
"""


def generate_pr_comment(template, diffs):
    response = requests.post(
        f"{GPT4_API_URL}/generate",
        json={"template": template, "diffs": diffs}
    )
    response.raise_for_status()
    return response.json()["generated_comment"]


def propose_command(description):
    cmd = f'echo "{description}"'
    comment = f'Proposed command: {cmd}'
    return cmd, comment


@click.group()
def cli():
    pass


@cli.command()
@click.option("--repo", required=True, help="Path to the Git repository")
@click.option("--source", required=True, help="Source branch")
@click.option("--target", required=True, help="Target branch")
@click.option("--template", help="Pull request template")
def gen_pr(repo, source, target, template):
    repo_path = os.path.abspath(repo)
    repo = Repo(repo_path)
    diffs = repo.git.diff(f"{source}...{target}")

    if not template:
        template = DEFAULT_PR_TEMPLATE

    template = template.strip()

    pr_comment = generate_pr_comment(template, diffs)
    click.echo(pr_comment)


@cli.command()
@click.option("--description", prompt="Command description", help="Description of the command to generate")
def gen_cmd(description):
    cmd, comment = propose_command(description)

    click.echo(comment)
    response = click.prompt("Accept the proposed command? (Y/N)", type=click.Choice(["Y", "N"]))

    if response == "Y":
        subprocess.call(cmd, shell=True)
        click.echo("Command executed successfully!")
    else:
        click.echo("Command rejected!")


if __name__ == "__main__":
    print('running cope pilot')
    cli()
