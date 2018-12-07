#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import getpass
import urlparse
import argparse
import requests
import ConfigParser

import subprocess as sp
from colorama import Fore, Back, Style, init

DEFAULT_GIT_API_URL = 'https://api.github.com'
DEFAULT_LOCAL_REPO_FOLDER = '.'

DEFAULT_GERRIT_PORT = 29418


def run_command(cmd, path='.', stop_on_error=True):
    """
    Run Command
    """

    if not cmd:
        return

    print(Fore.LIGHTBLUE_EX + cmd)

    process = sp.Popen(cmd, shell=True, cwd=path)
    process.communicate()
    exit_code = process.wait()

    if exit_code == 128 and stop_on_error == False:
        print(Fore.WHITE + Back.RED + 'ERROR: {0}'.format(exit_code))
    elif exit_code != 0 or stop_on_error == True:
        raise Exception("ERROR: Command exited with code: {0:d}".format(exit_code))


def get_github_repos(git_api_url,
                     config,
                     args,
                     git_repos,
                     two_factor_auth=None,
                     retry_count=0):
    """
    Gets GitHub repos
    """
    print(Fore.GREEN + git_api_url)

    if retry_count > 0:
        print(Fore.BLUE + "Retry Count: {0:d}".format(retry_count))

    headers = {
        'X-OAuth-Basic': config.get('github', 'github_token'),
        'X-OAuth-Scopes': 'repo, user',
        'X-Accepted-OAuth-Scopes': 'user'
    }

    if two_factor_auth is None and config.getboolean('auth', 'two_factor_auth'):
        two_factor_auth = str(input('Two-Factor Auth: '))

    if two_factor_auth is not None:
        headers['X-GitHub-OTP'] = two_factor_auth

    username = config.get('auth', 'username')

    password = ''
    if config.has_option('auth', 'password'):
        password = config.get('auth', 'password')
    else:
        password = getpass.getpass()

    response = requests.get(git_api_url,
                            headers=headers,
                            auth=(username, password))

    if not response.ok:
        print(Back.RED + Fore.WHITE + "Staus Code: {0:d}".format(response.status_code))

        if response.status_code == 401:
            if retry_count >= 3:
                raise Exception("Unable to authenticate: {0:s}".format(response.text))

            retry_count += 1
            get_github_repos(git_api_url,
                             config,
                             args,
                             git_repos,
                             two_factor_auth,
                             retry_count)

        raise Exception("Unable to connect\n{0:s}".format(response.text))

    # print(response.links)

    next_url = None
    if 'next' in response.links:
        next_url = response.links['next']['url']

    repos = json.loads(response.text)

    for repo in repos:
        git_repos.append(repo)

    if next_url:
        # print(Back.GREEN + Fore.BLACK + next_url)
        get_github_repos(next_url,
                         config,
                         args,
                         git_repos,
                         two_factor_auth,
                         retry_count)


def save_repo_list(git_repos, args):
    """
    Save Repo List
    """

    repo_json_filename = os.path.splitext(args.config_file)[0]
    repo_json_file = "{0:s}.json".format(repo_json_filename)
    print("Saving repo JSON file: {0:s}".format(repo_json_file))

    with open(repo_json_file, "wb") as repos_file:
        repos_file.write(json.dumps(git_repos,
                                    sort_keys=True,
                                    indent=4,
                                    separators=(',', ': ')))


def filter_git_repos(git_repos, args):
    """
    Process repos
    """
    filtered_repos = []
    if not args.repo_name_pattern:
        filtered_repos = git_repos
    else:
        for repo in git_repos:
            requested_repo_name = args.repo_name_pattern.lower()
            if requested_repo_name not in repo['name'].lower():
                if args.verbose:
                    print(repo['name'])

                continue
            else:
                filtered_repos.append(repo)

    return filtered_repos


def process_git_repos(selected_repos, args):
    """
    Process repos
    """
    repo_cnt = 0

    total_repos = len(selected_repos)
    for repo in selected_repos:
        repo_cnt += 1

        repo_percentage = (float(repo_cnt) / total_repos) * 100
        repo_str = "{0:d}/{1:d} ({2:.2f}%): {3:s}".format(repo_cnt,
                                                          total_repos,
                                                          repo_percentage,
                                                          repo['name'])

        path = os.path.abspath(repo['name'])

        print(Style.BRIGHT + repo_str)

        cmd = ''
        if not args.dont_rebase:
            cmd = 'git pull --rebase'

        if not os.path.isdir(path):
            path = '.'
            cmd = "git clone {0:s}".format(repo['ssh_url'])

        if not args.dry_run:
            run_command(cmd, path, args.stop_on_error)


def get_all_github_org_repos(args,
                             config,
                             git_repos):
    """
    Get all GitHub org repos
    """
    paths = ['orgs', config.get('github', 'org'), 'repos']
    url_path = '/'.join(x.strip('/') for x in paths if x)
    git_api_url = urlparse.urljoin(config.get('defaults', 'git_api_url'), url_path)
    git_api_url += '?type=all&per_page=250'

    get_github_repos(git_api_url,
                     config,
                     args,
                     git_repos)


def get_all_gerrit_org_repos(args,
                             config,
                             git_repos):
    """
    Get all Gerrit repos
    """

    # TODO: Implement SSH and Restful API versions
    gerrit_port = DEFAULT_GERRIT_PORT
    gerrit_server = 'gerrit-server'

    cmd = "ssh -p {0:d} bob_builder@{1:s}".format(gerrit_port, gerrit_server)
    cmd += " -o UserKnownHostsFile=/dev/null"
    cmd += " -o StrictHostKeyChecking=no"
    cmd += " -i ~/.ssh/bob_builder"
    cmd += " gerrit ls-projects"

    run_command(cmd)


def parse_args():
    """
    Parse arguments
    """
    desc = 'Downloads all or specificed repos from GitHub'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('repo_name_pattern',
                        nargs='?',
                        help='Repo Pattern')
    parser.add_argument('--config-file',
                        default='config.ini',
                        help='Configuration file')
    parser.add_argument('--repos-file',
                        help='Use previous JSON file')
    parser.add_argument('--update-list-only',
                        action='store_true',
                        default=False,
                        help='Update JSON file')
    parser.add_argument('--dont-rebase',
                        action='store_true',
                        default=False,
                        help="Don't pull rebase repos")
    parser.add_argument('--stop-on-error',
                        action='store_true',
                        default=False,
                        help="Stop on error")
    parser.add_argument('--dry-run',
                        action='store_true',
                        default=False,
                        help='Dry-run. No repos are downloaded')
    parser.add_argument('--verbose',
                        action='store_true',
                        default=False,
                        help='Verbose output')
    return parser.parse_args()


def parse_config(config_file, args):
    """
    Parse config file
    """
    config = ConfigParser.SafeConfigParser()
    config.read(args.config_file)

    if 'defaults' not in config.sections():
        config.add_section('defaults')

    if not config.has_option('auth', 'two_factor_auth'):
        config.set('auth', 'two_factor_auth', 'False')

    if not config.has_option('defaults', 'git_api_url'):
        config.set('defaults', 'git_api_url', DEFAULT_GIT_API_URL)

    return config


def main():
    """
    Main
    """
    git_repos = []

    # colorama init
    init(autoreset=True)

    args = parse_args()
    config = parse_config(args.config_file, args)

    if args.repo_name_pattern:
        print('Processing repos: ' + args.repo_name_pattern)

    if args.repos_file and not args.update_list_only:
        with open(args.repos_file) as data_file:
            git_repos = json.load(data_file)
    else:
        if config.has_section('github'):
            get_all_github_org_repos(args,
                                     config,
                                     git_repos)
        elif config.has_section('gerrit'):
            get_all_gerrit_org_repos(args,
                                     config,
                                     git_repos)

    repo_cnt = len(git_repos)

    if repo_cnt == 0:
        print(Fore.WHITE + Back.RED + 'ERROR: No repos found.')
        return

    save_repo_list(git_repos, args)

    print("Total Repos: {0:d}".format(repo_cnt))
    filtered_repos = filter_git_repos(git_repos, args)

    filtered_repos_percentage = (len(filtered_repos) / float(repo_cnt)) * 100
    print("Total Repos (filtered): {0:d} ({1:.2f}%)".format(len(filtered_repos),
                                                            filtered_repos_percentage))

    process_git_repos(filtered_repos, args)


if __name__ == '__main__':
    main()
