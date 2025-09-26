#!/usr/bin/env python3
"""CLI tool for reviewing GitHub Pull Requests using Shopify AI proxy with Gemini."""

import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import click
import yaml
from openai import AsyncOpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class PRReviewer:
    def __init__(self, cache_dir: str = '.cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Get OpenAI base URL from environment
        base_url = os.environ.get('OPENAI_BASE_URL')
        if not base_url:
            console.print(
                '[red]Error: OPENAI_BASE_URL environment variable must be set[/red]'
            )
            console.print(
                '[yellow]Example: export OPENAI_BASE_URL=https://api.openai.com/v1[/yellow]'
            )
            sys.exit(1)

        # Get API key from environment (may be dummy for some proxies)
        api_key = os.environ.get('OPENAI_API_KEY', 'dummy')

        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    def parse_pr_url(self, url: str) -> tuple[str, str, str]:
        """Parse GitHub PR URL to extract owner, repo, and PR number."""
        pattern = r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
        match = re.match(pattern, url)
        if not match:
            raise ValueError(f'Invalid GitHub PR URL: {url}')
        return match.groups()

    def run_gh_command(self, cmd: list[str]) -> str:
        """Run a GitHub CLI command and return the output."""
        try:
            result = subprocess.run(
                ['gh', *cmd], capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            console.print(f'[red]Error running gh command: {e.stderr}[/red]')
            sys.exit(1)

    def fetch_pr_data(self, owner: str, repo: str, pr_number: str) -> dict:
        """Fetch PR data using GitHub CLI."""
        console.print(f'[cyan]Fetching PR data for {owner}/{repo}#{pr_number}[/cyan]')

        # Get PR details
        pr_json = self.run_gh_command(
            [
                'pr',
                'view',
                pr_number,
                '--repo',
                f'{owner}/{repo}',
                '--json',
                'title,body,number,url,author',
            ]
        )
        pr_data = json.loads(pr_json)

        # Get PR diff
        diff = self.run_gh_command(
            ['pr', 'diff', pr_number, '--repo', f'{owner}/{repo}']
        )

        # Get changed files
        files_json = self.run_gh_command(
            ['pr', 'view', pr_number, '--repo', f'{owner}/{repo}', '--json', 'files']
        )
        files_data = json.loads(files_json)

        return {'pr': pr_data, 'diff': diff, 'files': files_data.get('files', [])}

    def load_prompt(self) -> str:
        """Load the Gemini review prompt from YAML file."""
        prompt_file = Path('gemini_prompt.yaml')
        if not prompt_file.exists():
            console.print('[red]Error: gemini_prompt.yaml not found[/red]')
            sys.exit(1)

        with open(prompt_file) as f:
            data = yaml.safe_load(f)
            return data['prompt']

    def get_cache_key(self, pr_data: dict) -> str:
        """Generate cache key from PR diff."""
        diff_hash = hashlib.sha256(pr_data['diff'].encode()).hexdigest()
        return f'pr_{pr_data["pr"]["number"]}_{diff_hash[:8]}'

    async def save_cache(self, cache_key: str, review: str):
        """Save review to cache."""
        cache_file = self.cache_dir / f'{cache_key}.json'
        with open(cache_file, 'w') as f:
            json.dump({'review': review}, f, indent=2)

    async def load_cache(self, cache_key: str) -> str | None:
        """Load review from cache."""
        cache_file = self.cache_dir / f'{cache_key}.json'
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                return data.get('review')
        return None

    async def review_pr(self, pr_data: dict) -> str:
        """Send PR data to Shopify proxy for review."""
        prompt = self.load_prompt()

        # Prepare context data
        pr_info = pr_data['pr']
        files_info = '\n'.join(
            [f.get('path', f.get('filename', 'unknown')) for f in pr_data['files']]
        )

        system_message = prompt
        repo_url = pr_info.get('url', '').split('/pull/')[0].replace(
            'https://github.com/', ''
        )
        user_message = f"""
Repository: {repo_url}
Pull Request Number: {pr_info['number']}
Title: {pr_info['title']}
Body: {pr_info.get('body', '')}

Files Changed:
{files_info}

Diff:
{pr_data['diff']}
"""

        console.print('[cyan]Sending PR for review...[/cyan]')

        try:
            response = await self.client.chat.completions.create(
                model='google:gemini-2.5-pro',
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_message},
                ],
            )

            return response.choices[0].message.content
        except Exception as e:
            console.print(f'[red]Error calling AI service: {e}[/red]')
            sys.exit(1)

    def post_review(self, owner: str, repo: str, pr_number: str, review: str):
        """Post review comment to GitHub using gh CLI."""
        console.print('[cyan]Posting review to GitHub...[/cyan]')

        # Create a temporary file with the review content
        temp_file = self.cache_dir / f'review_{pr_number}.md'
        with open(temp_file, 'w') as f:
            f.write(review)

        try:
            self.run_gh_command(
                [
                    'pr',
                    'comment',
                    pr_number,
                    '--repo',
                    f'{owner}/{repo}',
                    '--body-file',
                    str(temp_file),
                ]
            )

            console.print('[green]✓ Review posted successfully![/green]')

            # Clean up temp file
            temp_file.unlink()

        except Exception as e:
            console.print(f'[red]Error posting review: {e}[/red]')
            sys.exit(1)


@click.command()
@click.argument('pr_url')
@click.option(
    '--cache/--no-cache', default=True, help='Use cached results if available'
)
@click.option(
    '--dry-run', is_flag=True, help="Generate review but don't post to GitHub"
)
def main(pr_url: str, cache: bool, dry_run: bool):
    """Review a GitHub Pull Request using AI.

    PR_URL should be a full GitHub PR URL like:
    https://github.com/owner/repo/pull/123
    """
    reviewer = PRReviewer()

    try:
        # Parse PR URL
        owner, repo, pr_number = reviewer.parse_pr_url(pr_url)

        with Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            console=console,
        ) as progress:
            # Fetch PR data
            task = progress.add_task('Fetching PR data...', total=None)
            pr_data = reviewer.fetch_pr_data(owner, repo, pr_number)
            progress.update(task, description='PR data fetched')

            # Check cache
            cache_key = reviewer.get_cache_key(pr_data)
            review = None

            if cache:
                task = progress.add_task('Checking cache...', total=None)
                review = asyncio.run(reviewer.load_cache(cache_key))
                if review:
                    progress.update(task, description='Using cached review')
                    console.print('[yellow]Using cached review[/yellow]')
                else:
                    progress.update(task, description='No cache found')

            # Generate review if not cached
            if not review:
                task = progress.add_task('Generating AI review...', total=None)
                review = asyncio.run(reviewer.review_pr(pr_data))
                progress.update(task, description='Review generated')

                # Save to cache
                if cache:
                    asyncio.run(reviewer.save_cache(cache_key, review))

            # Display review
            console.print('\n[bold]Generated Review:[/bold]')
            console.print(review)

            # Post review unless dry run
            if not dry_run:
                reviewer.post_review(owner, repo, pr_number, review)
            else:
                console.print('\n[yellow]Dry run mode - review not posted[/yellow]')

    except Exception as e:
        console.print(f'[red]Error: {e}[/red]')
        sys.exit(1)


if __name__ == '__main__':
    main()
