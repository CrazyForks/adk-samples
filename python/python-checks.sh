#!/bin/bash
#
# python-checks.sh: Runs formatting and linting checks on Python files based on arguments.
#
set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
AGENTS_DIR="./agents"
NOTEBOOKS_DIR="./notebooks"
AGENT_CHECK_PATH=""
NOTEBOOK_CHECK_PATH=""
ACTION=""
CLEAN_CHECKS=()

# --- Function Definitions ---

show_help() {
    echo "
Usage: ./python-checks.sh <ACTION> [PATH_OPTION] [CHECK]...

This script runs Python formatting (Black, iSort) and linting (Flake8) checks.

<ACTION> (Required Positional Argument):
  check                       Executes the specified quality checks.
  help                        Displays this help message.

Path Options (Used with 'check' action):
  --agent FOLDER_NAME         Checks a specific agent subfolder (e.g., NEW_AGENT_NAME) inside ./agents.
  --notebook FOLDER_NAME      Checks a specific notebook subfolder (e.g., NEW_NOTEBOOK_NAME) inside ./notebooks.

Available Checks (Used with 'check' action):
  all                         Runs all checks: black, isort, and flake8. (Default if no checks specified)
  black                       Runs the Black auto-formatter check only.
  isort                       Runs the iSort import sorter check only.
  lint, flake8                Runs the Flake8 linter check only.

Examples:
  # 1. Run Black and iSort on a specific new agent folder:
  ./python-checks.sh check --agent new_sales_agent black isort

  # 2. Run all checks (black, isort, flake8) on a specific notebook folder:
  ./python-checks.sh check --notebook documentation_updates all
"
    exit 0
}

run_black() {
    echo -e "\n--- Running Black Formatting Check ---"
    if [ -n "$AGENT_CHECK_PATH" ]; then
        # Agents directory check
        black --check --diff "$AGENT_CHECK_PATH"
        echo -e "Black check passed for agent directory: $AGENT_CHECK_PATH"
    elif [ -n "$NOTEBOOK_CHECK_PATH" ]; then
        # Notebooks directory check
        nbqa black --check --diff "$NOTEBOOK_CHECK_PATH"
        echo -e "Black check passed for notebook directory: $NOTEBOOK_CHECK_PATH"
    fi
}

run_isort() {
    echo -e "\n--- Running iSort Import Check ---"
    if [ -n "$AGENT_CHECK_PATH" ]; then
        # Agents directory check
        isort --check-only --diff "$AGENT_CHECK_PATH"
        echo -e "iSort check passed for agent directory: $AGENT_CHECK_PATH"
    elif [ -n "$NOTEBOOK_CHECK_PATH" ]; then
        # Notebooks directory check
        nbqa isort --check-only --diff "$NOTEBOOK_CHECK_PATH"
        echo -e "iSort check passed for notebook directory: $NOTEBOOK_CHECK_PATH"
    fi
}

run_flake8() {
    echo -e "\n--- Running Flake8 Linting Check ---"
    if [ -n "$AGENT_CHECK_PATH" ]; then
        # Agents directory check
        flake8 "$AGENT_CHECK_PATH"
        echo -e "Flake8 check passed for agent directory: $AGENT_CHECK_PATH"
    elif [ -n "$NOTEBOOK_CHECK_PATH" ]; then
        # Notebooks directory check
        # We check if the folder exists first, as the final path validation should handle this.
        if [ -d "$NOTEBOOK_CHECK_PATH" ]; then
            nbqa flake8 "$NOTEBOOK_CHECK_PATH"
            echo -e "Flake8 check passed for notebook directory: $NOTEBOOK_CHECK_PATH"
        else
            echo "Error: Notebook directory '$NOTEBOOK_CHECK_PATH' not found."
            exit 1
        fi
    fi
}

check_and_install_tools() {
    REQUIRED_TOOLS="black flake8 isort nbqa"
    TOOLS_MISSING=0

    for tool in $REQUIRED_TOOLS; do
        if ! command -v $tool &> /dev/null; then
            TOOLS_MISSING=1
            break
        fi
    done

    if [ $TOOLS_MISSING -eq 1 ]; then
        echo "Installing required Python tools ($REQUIRED_TOOLS)..."
        python3 -m pip install $REQUIRED_TOOLS
    fi
}

# --- Argument Parsing ---

# Check for required action argument
if [ $# -eq 0 ]; then
    echo "Error: Missing action. Use './python-checks.sh help' for usage."
    exit 1
fi

# The first argument is the action
ACTION="$1"
shift # Consume the action argument

case "$ACTION" in
    help)
        show_help
        ;;
    check)
        # Continue parsing remaining arguments for check options
        ;;
    *)
        echo "Error: Invalid action '$ACTION'. Use './python-checks.sh help' for usage."
        exit 1
        ;;
esac

# --- Parse Check Options (Only if ACTION is 'check') ---

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent)
            if [ -n "$NOTEBOOK_CHECK_PATH" ]; then
                echo "Error: Cannot use --agent and --notebook together."
                exit 1
            fi
            if [ -z "$2" ] || [[ "$2" == --* ]]; then
                echo "Error: --agent requires a folder name."
                exit 1
            fi
            # CRITICAL CHANGE: Build the path relative to the base directory
            AGENT_CHECK_PATH="$AGENTS_DIR/$2"
            shift 2
            continue
            ;;
        --notebook)
            if [ -n "$AGENT_CHECK_PATH" ]; then
                echo "Error: Cannot use --agent and --notebook together."
                exit 1
            fi
            if [ -z "$2" ] || [[ "$2" == --* ]]; then
                echo "Error: --notebook requires a folder name."
                exit 1
            fi
            # CRITICAL CHANGE: Build the path relative to the base directory
            NOTEBOOK_CHECK_PATH="$NOTEBOOKS_DIR/$2"
            shift 2
            continue
            ;;
        *)
            # Everything else is considered a specific check (black, isort, lint, all)
            CLEAN_CHECKS+=("$1")
            shift 1
            continue
            ;;
    esac
done

# --- Main Execution (Action: check) ---

# 1. Enforce Path Option
if [ -z "$AGENT_CHECK_PATH" ] && [ -z "$NOTEBOOK_CHECK_PATH" ]; then
    echo "Error: When using action 'check', you must specify either '--agent FOLDER_NAME' or '--notebook FOLDER_NAME'."
    exit 1
fi

# 2. Validate paths exist (now checking for directory existence for both)
if [ -n "$AGENT_CHECK_PATH" ] && [ ! -d "$AGENT_CHECK_PATH" ]; then
    echo "Error: Agent directory '$AGENT_CHECK_PATH' not found."
    exit 1
fi

if [ -n "$NOTEBOOK_CHECK_PATH" ] && [ ! -d "$NOTEBOOK_CHECK_PATH" ]; then
    echo "Error: Notebook directory '$NOTEBOOK_CHECK_PATH' not found."
    exit 1
fi

# 3. Determine checks to run (Default to 'all' if no checks provided)
RUN_ALL=false
if [ ${#CLEAN_CHECKS[@]} -eq 0 ] || [[ " ${CLEAN_CHECKS[@]} " =~ " all " ]]; then
    RUN_ALL=true
fi

echo "Starting local Python code quality checks..."

# 4. Install Tools
check_and_install_tools

# 5. Execute Checks
if [ "$RUN_ALL" = true ]; then
    run_black
    run_isort
    run_flake8
else
    # Validate and run specific checks
    for check in "${CLEAN_CHECKS[@]}"; do
        case "$check" in
            black)
                run_black
                ;;
            isort)
                run_isort
                ;;
            lint | flake8)
                run_flake8
                ;;
            *)
                echo "Error: Unknown check '$check'. Use './python-checks.sh help' for valid checks."
                exit 1
                ;;
        esac
    done
fi

echo -e "\n✅ All requested Python checks completed successfully!"