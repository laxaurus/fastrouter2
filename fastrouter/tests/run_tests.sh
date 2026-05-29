#!/usr/bin/env bash
#
# FastRouter Test Runner
#
# Runs the full test suite with real dependencies (PostgreSQL, Redis).
# Requires DATABASE_URL and REDIS_URL environment variables.
#
# Usage:
#   ./tests/run_tests.sh              # All tests
#   ./tests/run_tests.sh -v           # Verbose
#   ./tests/run_tests.sh -k "auth"    # Filter by keyword
#   ./tests/run_tests.sh -m "not slow" # Skip slow tests
#
# Options:
#   -v, --verbose       Verbose output
#   -k PATTERN           Run tests matching pattern
#   -m MARKERS           Pytest markers (e.g., "not slow")
#   -x                   Stop on first failure
#   --log-dir DIR        Directory for test logs (default: tests/logs)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${SCRIPT_DIR}/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Defaults
VERBOSE=""
FILTER=""
MARKERS=""
STOP_ON_FIRST=""

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -x)
            STOP_ON_FIRST="-x"
            shift
            ;;
        -k)
            FILTER="-k $2"
            shift 2
            ;;
        -m)
            MARKERS="-m $2"
            shift 2
            ;;
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-v] [-k pattern] [-m markers] [-x] [--log-dir dir]"
            exit 1
            ;;
    esac
done

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Set defaults if env vars not already set
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://fastrouter:fastrouter@localhost:5432/fastrouter_test}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export LITELLM_URL="${LITELLM_URL:-http://localhost:4000}"
export JWT_SECRET="${JWT_SECRET:-test-jwt-secret-key}"
export ENCRYPTION_KEY="${ENCRYPTION_KEY:-test-32-byte-encryption-key!!}"
export LITELLM_MASTER_KEY="${LITELLM_MASTER_KEY:-sk-test-master-key}"
export STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-}"
export STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-}"
export STRIPE_PRICE_ID="${STRIPE_PRICE_ID:-}"

echo "======================================"
echo "  FastRouter Test Suite"
echo "======================================"
echo "Database: $DATABASE_URL"
echo "Redis:    $REDIS_URL"
echo "LiteLLM:  $LITELLM_URL"
echo "Stripe:   ${STRIPE_SECRET_KEY:+configured}${STRIPE_SECRET_KEY:-not configured}"
echo "Log dir:  $LOG_DIR"
echo "======================================"
echo ""

# Check dependencies
if ! python -c "import redis" 2>/dev/null; then
    echo "ERROR: redis-py not installed. Run: pip install redis"
    exit 1
fi

LOG_FILE="$LOG_DIR/test_${TIMESTAMP}.log"

# Run tests
echo "Running tests..."
set +e
cd "$PROJECT_DIR"
python -m pytest \
    tests/ \
    ${MARKERS:--m "not integration"} \
    $VERBOSE \
    $FILTER \
    $STOP_ON_FIRST \
    --tb=short \
    --capture=no \
    --strict-markers \
    --color=yes \
    2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}
set -e

echo ""
echo "======================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "  ALL TESTS PASSED"
else
    echo "  TESTS FAILED (exit code: $EXIT_CODE)"
fi
echo "  Log saved: $LOG_FILE"
echo "======================================"

exit $EXIT_CODE
