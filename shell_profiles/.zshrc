
# Clones a git repo into folder structure (<USERNAME>/<REPO_NAME>) and then cd into it.
function gitc() {
  local command_line_args repo_folder

  if [ -z "$1" ]; then
    echo "ERROR Git repo not defined."
    echo "Usage: -"
    echo "  gitc <GIT_REPO>"
    echo ""
    echo "e.g."
    echo "  gitc git@github.com:jpnewman/jenkins-scripts.git"
    return
  fi

  command_line_args="$1"
  repo_folder=$(sed 's/^.*:\/\///; s/github.com\///; s/\.git$//' <<< $command_line_args)

  echo "$repo_folder"

  git clone $command_line_args $repo_folder
  cd $repo_folder
}
