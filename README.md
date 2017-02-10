# DownloadRepos

This script downloads GitHub organization repositories and is useful if you have lots of repos you would like to ```clone``` or ```pull --rebase```.

## Install Python requirements

~~~bash
pip install -r requirements.txt
~~~

## Download repos

~~~
./DownloadRepos.py ansible --verbose
~~~

## Download previous repos

> No authenticate needed

~~~
./DownloadRepos.py ansible --repos-file config.json
~~~

## Dry run

~~~
./DownloadRepos.py ansible --dry-run


./DownloadRepos.py ansible --repos-file config.json --dry-run
./DownloadRepos.py --repos-file config.json --dry-run
~~~

## Update List Only

~~~
./DownloadRepos.py --update-list-only
~~~

## Command Line Arguments

|Name|Description|Default Value|
|---|---|---|
|*First Positional Argument*|Repo Name Pattern||
|```--config-file```|Configuration file|config.ini|
|```--repos-file```|Use previous JSON file||
|```--update-list-only```|Update JSON file||
|```--rebase```|Pull rebase repos|True|
|```--dry-run```|Dry-run. No repos are downloaded|False|
|```--verbose```|Verbose output|False|

## Configuration File (config.ini)

Section ```[github]```

|Key|Description|Default Value|
|---|---|---|
|org|Organization||
|github_token|GitHub\_API_Token||

Section ```[auth]```

|Key|Description|Default Value|
|---|---|---|
|username|Username||
|password|Password||
|two\_factor_auth|Use Two Factor Auth|True|

Section ```[local]```

|Key|Description|Default Value|
|---|---|---|
|repo\_base_folder|local repo base path|.|


## Create GitHub Token

<https://help.github.com/articles/creating-an-access-token-for-command-line-use/>

## Lint Script

~~~
flake8 DownloadRepos.py
~~~

## Tested

Only tested on Mac OS X

## Zsh function

File ```./shell_profiles/.zshrc``` contains a function called ```gitc``` that can be used to clone a git repo into folder structure (```<USERNAME>/<REPO_NAME>```) and then ```cd``` into it.

*e.g.*

~~~
gitc git@github.com:jpnewman/download_repos.git
~~~

## License

MIT / BSD

## Author Information

John Paul Newman
