set -eo pipefail

COLOR_GREEN=$(tput setaf 2)
COLOR_BLUE=$(tput setaf 4)
COLOR_RED=$(tput setaf 1)
COLOR_NC=$(tput sgr0)  # reset color

cd "$(dirname "$(realpath "$0")")/.."  # symbolic link "$0"

echo "${COLOR_BLUE}Starting black${COLOR_NC}"
uv run black .
echo "OK"

echo "${COLOR_BLUE}Start Ruff Auto Fix${COLOR_NC}"
uv run ruff check --select I --fix . || true
echo "${COLOR_GREEN}Auto-fix Done${COLOR_NC}"

echo "${COLOR_BLUE}Run Mypy${COLOR_NC}"
if ! uv run mypy . ; then
  echo ""
  echo "${COLOR_RED}✖ Mypy found issues.${COLOR_NC}"
  echo "${COLOR_RED}→ Please fix the issues above manually and re-run the command.${COLOR_NC}"
  exit 1
fi

echo "${COLOR_GREEN}All tests passed successfully!${COLOR_NC}"
