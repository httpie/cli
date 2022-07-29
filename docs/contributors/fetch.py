"""
Generate the contributors database.

FIXME: replace `requests` calls with the HTTPie API, when available.
"""
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from subprocess import check_output
from time import sleep
from typing import Any, Dict, Optional, Set

import requests

FullNames = Set[str]
GitHubLogins = Set[str]
Person = Dict[str, str]
People = Dict[str, Person]
UserInfo = Dict[str, Any]

CO_AUTHORS = re.compile(r'Co-authored-by: ([^<]+) <').finditer
API_URL = 'https://api.github.com'
REPO = OWNER = 'httpie'
REPO_URL = f'{API_URL}/repos/{REPO}/{OWNER}'

HERE = Path(__file__).parent
DB_FILE = HERE / 'people.json'

DEFAULT_PERSON: Person = {'committed': [], 'reported': [], 'github': '', 'twitter': ''}
SKIPPED_LABELS = {'invalid'}

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
assert GITHUB_TOKEN, 'GITHUB_TOKEN envar is missing'


class FinishedForNow(Exception):
    """Raised when remaining GitHub rate limit is zero."""


def main(previous_release: str, current_release: str) -> int:
    since = release_date(previous_release)
    until = release_date(current_release)

    contributors = load_awesome_people()
    try:
        committers = find_committers(since, until)
        reporters = find_reporters(since, until)
    except Exception as exc:
        # We want to save what we fetched so far. So pass.
        print(' !! ', exc)

    try:
        merge_all_the_people(current_release, contributors, committers, reporters)
        fetch_missing_users_details(contributors)
    except FinishedForNow:
        # We want to save what we fetched so far. So pass.
        print(' !! Committers:', committers)
        print(' !! Reporters:', reporters)
        exit_status = 1
    else:
        exit_status = 0

    save_awesome_people(contributors)
    return exit_status


def find_committers(since: str, until: str) -> FullNames:
    url = f'{REPO_URL}/commits'
    page = 1
    per_page = 100
    params = {
        'since': since,
        'until': until,
        'per_page': per_page,
    }
    committers: FullNames = set()

    while 'there are commits':
        params['page'] = page
        data = fetch(url, params=params)

        for item in data:
            commit = item['commit']
            committers.add(commit['author']['name'])
            debug(' >>> Commit', item['html_url'])
            for co_author in CO_AUTHORS(commit['message']):
                name = co_author.group(1)
                committers.add(name)

        if len(data) < per_page:
            break
        page += 1

    return committers


def find_reporters(since: str, until: str) -> GitHubLogins:
    url = f'{API_URL}/search/issues'
    page = 1
    per_page = 100
    params = {
        'q': f'repo:{REPO}/{OWNER} is:issue closed:{since}..{until}',
        'per_page': per_page,
    }
    reporters: GitHubLogins = set()

    while 'there are issues':
        params['page'] = page
        data = fetch(url, params=params)

        for item in data['items']:
            # Filter out unwanted labels.
            if any(label['name'] in SKIPPED_LABELS for label in item['labels']):
                continue
            debug(' >>> Issue', item['html_url'])
            reporters.add(item['user']['login'])

        if len(data['items']) < per_page:
            break
        page += 1

    return reporters


def merge_all_the_people(release: str, contributors: People, committers: FullNames, reporters: GitHubLogins) -> None:
    """
    >>> contributors = {'Alice': new_person(github='alice', twitter='alice')}
    >>> merge_all_the_people('2.6.0', contributors, {}, {})
    >>> contributors
    {'Alice': {'committed': [], 'reported': [], 'github': 'alice', 'twitter': 'alice'}}

    >>> contributors = {'Bob': new_person(github='bob', twitter='bob')}
    >>> merge_all_the_people('2.6.0', contributors, {'Bob'}, {'bob'})
    >>> contributors
    {'Bob': {'committed': ['2.6.0'], 'reported': ['2.6.0'], 'github': 'bob', 'twitter': 'bob'}}

    >>> contributors = {'Charlotte': new_person(github='charlotte', twitter='charlotte', committed=['2.5.0'], reported=['2.5.0'])}
    >>> merge_all_the_people('2.6.0', contributors, {'Charlotte'}, {'charlotte'})
    >>> contributors
    {'Charlotte': {'committed': ['2.5.0', '2.6.0'], 'reported': ['2.5.0', '2.6.0'], 'github': 'charlotte', 'twitter': 'charlotte'}}

    """
    # Update known contributors.
    for name, details in contributors.items():
        if name in committers:
            if release not in details['committed']:
                details['committed'].append(release)
            committers.remove(name)
        if details['github'] in reporters:
            if release not in details['reported']:
                details['reported'].append(release)
            reporters.remove(details['github'])

    # Add new committers.
    for name in committers:
        user_info = user(fullname=name)
        contributors[name] = new_person(
            github=user_info['login'],
            twitter=user_info['twitter_username'],
            committed=[release],
        )
        if user_info['login'] in reporters:
            contributors[name]['reported'].append(release)
            reporters.remove(user_info['login'])

    # Add new reporters.
    for github_username in reporters:
        user_info = user(github_username=github_username)
        contributors[user_info['name'] or user_info['login']] = new_person(
            github=github_username,
            twitter=user_info['twitter_username'],
            reported=[release],
        )


def release_date(release: str) -> str:
    date = check_output(['git', 'log', '-1', '--format=%ai', release], text=True).strip()
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S %z').isoformat()


def load_awesome_people() -> People:
    try:
        with DB_FILE.open(encoding='utf-8') as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError):
        return {}


def fetch(url: str, params: Optional[Dict[str, str]] = None) -> UserInfo:
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authentication': f'token {GITHUB_TOKEN}'
    }
    for retry in range(1, 6):
        debug(f'[{retry}/5]', f'{url = }', f'{params = }')
        with requests.get(url, params=params, headers=headers) as req:
            try:
                req.raise_for_status()
            except requests.exceptions.HTTPError as exc:
                if exc.response.status_code == 403:
                    # 403 Client Error: rate limit exceeded for url: ...
                    now = int(datetime.utcnow().timestamp())
                    xrate_limit_reset = int(exc.response.headers['X-RateLimit-Reset'])
                    wait = xrate_limit_reset - now
                    if wait > 20:
                        raise FinishedForNow()
                    debug(' !', 'Waiting', wait, 'seconds before another try ...')
                    sleep(wait)
                continue
            return req.json()
    assert ValueError('Rate limit exceeded')


def new_person(**kwargs: str) -> Person:
    data = deepcopy(DEFAULT_PERSON)
    data.update(**kwargs)
    return data


def user(fullname: Optional[str] = '', github_username: Optional[str] = '') -> UserInfo:
    if github_username:
        url = f'{API_URL}/users/{github_username}'
        return fetch(url)

    url = f'{API_URL}/search/users'
    for query in (f'fullname:{fullname}', f'user:{fullname}'):
        params = {
            'q': f'repo:{REPO}/{OWNER} {query}',
            'per_page': 1,
        }
        user_info = fetch(url, params=params)
        if user_info['items']:
            user_url = user_info['items'][0]['url']
            return fetch(user_url)


def fetch_missing_users_details(people: People) -> None:
    for name, details in people.items():
        if details['github'] and details['twitter']:
            continue
        user_info = user(github_username=details['github'], fullname=name)
        if not details['github']:
            details['github'] = user_info['login']
        if not details['twitter']:
            details['twitter'] = user_info['twitter_username']


def save_awesome_people(people: People) -> None:
    with DB_FILE.open(mode='w', encoding='utf-8') as fh:
        json.dump(people, fh, indent=4, sort_keys=True)
        fh.write("\n")


def debug(*args: Any) -> None:
    if os.getenv('DEBUG') == '1':
        print(*args)


if __name__ == '__main__':
    ret = 1
    try:
        ret = main(*sys.argv[1:])
    except TypeError:
        ret = 2
        print(f'''
Fetch contributors to a release.

Usage:
    python {sys.argv[0]} {sys.argv[0]} <RELEASE N-1> <RELEASE N>
Example:
    python {sys.argv[0]} 2.4.0 2.5.0

Define the DEBUG=1 environment variable to enable verbose output.
''')
    except KeyboardInterrupt:
        ret = 255
    sys.exit(ret)
