set -eo pipefail

COLOR_GREEN=$(tput setaf 2)
COLOR_BLUE=$(tput setaf 4)
COLOR_RED=$(tput setaf 1)
COLOR_NC=$(tput sgr0)

cd "$(dirname "$(realpath "$0")")/.."

echo "${COLOR_BLUE}Run tests${COLOR_NC}"

if ! docker exec mysql true 2>/dev/null; then
  echo "${COLOR_RED}✖ MySQL container not running${COLOR_NC}"
  exit 1
fi

echo "${COLOR_BLUE}Run Pytest${COLOR_NC}"

if ! uv run pytest tests --cov=app --cov-report=term-missing; then
  echo ""
  echo "${COLOR_RED}✖ Tests failed${COLOR_NC}"
  exit 1
fi

echo "${COLOR_GREEN}✔ Tests passed${COLOR_NC}"
