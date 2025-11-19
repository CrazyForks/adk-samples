#!/bin/bash
#
# check-python.sh: Runs formatting and linting checks on Python files based on arguments.
#
set -e # <-- RE-ENABLED: Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
AGENTS_DIR="./agents"
NOTEBOOKS_DIR="./notebooks"
CHECKS_TO_RUN=()
RUN_COMMAND=false

# --- Function Definitions (unchanged) ---

show_help() {
    echo "
Usage: ./check-python.sh [OPTION] [CHECK]...

Runs Python formatting (Black, iSort) and linting (Flake8) checks 
on the 'python/agents/' and 'python/notebooks/' directories.

Options:
  --help                      Displays this help message.
  --run [CHECK]...            Executes the specified checks. If no CHECK is provided, 
                              it defaults to running all checks (black, isort, and flake8).

Available Checks (CHECK):
  all                         Runs all checks: black, isort, and flake8.
  black                       Runs the Black auto-formatter check only.
  isort                       Runs the iSort import sorter check only.
  lint, flake8                Runs the Flake8 linter check only. (Aliases for linting)
"
    exit 0
}

run_black() {
    echo -e "\n--- Running Black Formatting Check (.py files) ---"
    black --check --diff $AGENTS_DIR
    
    echo -e "\n--- Running Black Check on Notebooks (.ipynb) ---"
    nbqa black --check --diff $NOTEBOOKS_DIR
}

run_isort() {
    echo -e "\n--- Running iSort Import Check (.py files) ---"
    isort --check-only --diff $AGENTS_DIR

    echo -e "\n--- Running iSort Check on Notebooks (.ipynb) ---"
    nbqa isort --check-only --diff $NOTEBOOKS_DIR
}

run_flake8() {
    echo -e "\n--- Running Flake8 Linting Check (.py files) ---"
    flake8 $AGENTS_DIR

    echo -e "\n--- Running Flake8 Linting Check on Notebooks (.ipynb) ---"
    nbqa flake8 $NOTEBOOKS_DIR
}

# --- Argument Parsing Loop (unchanged) ---

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help)
            show_help
            ;;
        --run)
            RUN_COMMAND=true
            # Shift the --run option off, leaving only the checks
            shift 
            # Break the loop here to process the remaining arguments as checks
            break 
            ;;
        *)
            # If we hit an argument we don't recognize, show error/help
            echo "Error: Unknown option '$1'. Use './check-python.sh --help' for options."
            exit 1
            ;;
    esac
    # Shift to the next argument
    shift
done

# --- Main Execution (The necessary logic that was missing) ---

# Handle case where only './check-python.sh' is run without options
if [[ "$RUN_COMMAND" == false && "$#" -eq 0 ]]; then
    echo "Error: Missing '--run' option. Use './check-python.sh --help' for options."
    exit 1
fi

# After parsing, all remaining arguments are stored in positional parameters ($@)
CHECKS_TO_RUN=("$@")

# If --run was used with no further arguments, default to 'all'
if [[ "$RUN_COMMAND" == true && ${#CHECKS_TO_RUN[@]} -eq 0 ]]; then
    CHECKS_TO_RUN=("all")
fi

echo "Starting local Python code quality checks..."

# --- Tool Installation Check (FIXED LOGIC) ---
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
    # Use python3 -m pip install for maximum environment safety
    python3 -m pip install $REQUIRED_TOOLS
fi

# --- Determine which checks to run ---
RUN_ALL=false
CLEAN_CHECKS=()
for check in "${CHECKS_TO_RUN[@]}"; do
    case "$check" in
        all)
            RUN_ALL=true
            break
            ;;
        black | isort | lint | flake8)
            CLEAN_CHECKS+=("$check")
            ;;
        *)
            echo "Error: Unknown check '$check'. Use './check-python.sh --help' for valid checks."
            exit 1
            ;;
    esac
done

# --- Execute Checks (THE MISSING LOGIC) ---
if $RUN_ALL; then
    run_black
    run_isort
    run_flake8
else
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
        esac
    done
fi

echo -e "\n✅ All requested Python checks completed successfully!"