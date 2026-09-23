#!/bin/bash
# Detects the current Celesta service from the working directory and injects
# the SDD command templates (.claude/commands/spec.md and plan.md) if they exist.
# Runs on every UserPromptSubmit. Outputs nothing if not inside a known Celesta service.

CWD="${PWD:-$(pwd)}"

SERVICES=(
  celesta-payment
  celesta-wallet
  celesta-backoffice
  celesta-sportsbetting
  celesta-sb-wallet
  celesta-game-go
  celesta-game
  celesta-promotion
  celesta-crm
  celesta-fraud
  celesta-segment
  celesta-activity
  celesta-statistics
  celesta-notification
  celesta-contact
  celesta-scenario
  celesta-sensor
  celesta-cms-v2
  celesta-cms
  celesta-brand
  celesta-gateway
  celesta-backoffice-front
  celesta-website
  casino-gateway
  celesta-scripts
  shared-libs
)

SERVICE=""
PROJECT_ROOT=""
for s in "${SERVICES[@]}"; do
  if [[ "$CWD" == *"/$s"* ]]; then
    SERVICE="$s"
    PROJECT_ROOT="${CWD%%/$s*}/$s"
    break
  fi
done

if [ -z "$SERVICE" ]; then
  exit 0
fi

echo "<celesta-context service=\"$SERVICE\">"

SPEC="$PROJECT_ROOT/.claude/commands/spec.md"
PLAN="$PROJECT_ROOT/.claude/commands/plan.md"

if [ -f "$SPEC" ]; then
  echo "<spec-template>"
  cat "$SPEC"
  echo "</spec-template>"
fi

if [ -f "$PLAN" ]; then
  echo "<plan-template>"
  cat "$PLAN"
  echo "</plan-template>"
fi

echo "</celesta-context>"
