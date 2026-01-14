#!/bin/bash
while true; do
  result=$(claude -p "Read PRD.md. Pick ONE unchecked task. Implement it. Commit.
  If the PRD is complete, output <promise>COMPLETE</promise>.")

  if [[ "$result" == *"COMPLETE"* ]]; then
    echo "All done!"
    break
  fi
done
