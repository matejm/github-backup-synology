import os
import subprocess
import datetime
import re
import http.client
import json
from urllib.parse import urlencode
from typing import List, Optional
import argparse

parser = argparse.ArgumentParser(
    prog='Backup GitHub repositories',
    description='Backup all repositories from a GitHub organization or user to a directory. Has basic support for incremental backups.')

parser.add_argument(
    '--organization', help='The organization to backup (e.g. zerodays). If set, the user argument is ignored.')
parser.add_argument(
    '--user', help='The user to backup (e.g. matejm). Will be ignored if organization is set.')
parser.add_argument(
    '--token', help='Personal access token (fine-grained token with Repository contents and metadata permissions for all repositories you want to backup)')
parser.add_argument(
    '--path', help='Where you want to store backed-up repositories. Should be an absolute path (no trailing slash). Do not use the same directory for backups from multiple organizations or users.')

args = parser.parse_args()

if args.organization is None and args.user is None:
    print('You need to set either organization or user to backup!')
    parser.print_help()
    exit(1)

if args.path is None:
    parser.print_help()
    exit(1)

if args.token is None:
    print('🚨 Warning: You did not provide a token. This will only work for public repositories.')

DATE_FORMAT_STRING = '%Y-%m-%d-%H-%M-%S'
CLEAN_REPO_NAME = re.compile(r'[^a-zA-Z0-9-]')


def repos(org: Optional[str] = None, user: Optional[str] = None):
    """
    Generator that fetches all repositories for the given organization or user.
    """
    if org is None and user is None:
        raise Exception('You need to set either org or user to backup')

    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'backup.py'
    }
    if args.token is not None:
        headers['Authorization'] = f'Bearer {args.token}'

    page_size = 100

    for page in range(1, 100):  # max 10 000 repos, should be enough
        params = {
            'type': 'all',
            'per_page': page_size,
            'page': page,
            # sort by updated to get the most recently updated repos first,
            # these are the ones we probably want to backup
            'sort': 'updated',
            'direction': 'desc'
        }

        if org is not None:
            path = f'orgs/{org}/repos'
        else:
            path = f'users/{user}/repos'

        # Make the GET request
        conn.request(
            "GET",
            f"/{path}?{urlencode(params)}",
            headers=headers
        )
        response = conn.getresponse()

        if response.status == 200:
            response_str = response.read().decode()
            if not response_str:
                # No more repos
                break

            # Parse the JSON response
            repos = json.loads(response_str)
            for repo in repos:
                yield repo

            if len(repos) < page_size:
                # This should be the last page
                break
        else:
            # Raise an error if the response status is not 200
            raise Exception(
                f"Failed to fetch repos: {response.status} - {response.reason}")

    conn.close()


def find_latest_backup(all_backups_dir: str, old_backups: List[str], cloned_name: str):
    """
    Go through the old backups and find the latest backup for the repo.
    """
    for backup in old_backups:
        if os.path.exists(os.path.join(all_backups_dir, backup, cloned_name)):
            return datetime.datetime.strptime(backup, DATE_FORMAT_STRING)
    return None


def main():
    all_backups_dir = args.path

    current_backup_dir = os.path.join(
        all_backups_dir, datetime.datetime.now().strftime(DATE_FORMAT_STRING)
    )
    os.makedirs(current_backup_dir, exist_ok=True)

    old_backups = os.listdir(all_backups_dir)
    # iso date format is sortable - newest first
    old_backups.sort(reverse=True)

    stats = {
        'cloned': 0,
        'skipped': 0
    }

    for repo in repos(org=args.organization, user=args.user):
        print(f'📦 {repo["full_name"]}')

        # Clean repo name just in case
        cleaned_name = CLEAN_REPO_NAME.sub('', repo['name'])
        cloned_name = f'{cleaned_name}.git'

        # Check when the repo was last updated
        updated_at = datetime.datetime.strptime(
            repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ'
        )

        latest_backup_date = find_latest_backup(
            all_backups_dir, old_backups, cloned_name)

        if latest_backup_date is not None:
            latest_str = latest_backup_date.strftime(DATE_FORMAT_STRING)
            if updated_at < latest_backup_date:
                print(
                    f'✔️ Latest version already backed up in {latest_str}'
                )
                stats['skipped'] += 1
                continue

            updated_str = updated_at.strftime(DATE_FORMAT_STRING)
            print(f'last backup {latest_str}, updated at {updated_str}')

        path = f'{args.organization}/{repo["name"]}' if args.organization else f'{args.user}/{repo["name"]}'
        # Clone the repo
        subprocess.check_call([
            'git', 'clone',  '--mirror',
            f'https://oauth2:{args.token}@github.com/{path}' if args.token else repo["clone_url"],
            cloned_name
        ], cwd=current_backup_dir)

        stats['cloned'] += 1
        print(f'💾 Cloned.')

    print(
        f'📊 Checked {stats["cloned"] + stats["skipped"]} repositories, cloned {stats["cloned"]} and skipped {stats["skipped"]}')


if __name__ == '__main__':
    main()
