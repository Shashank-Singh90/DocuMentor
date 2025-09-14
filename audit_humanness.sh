#!/bin/bash
echo "=== DocuMentor Human Artifacts Audit ==="
echo "TODOs: $(grep -r "TODO" src/ api_server.py | wc -l)"
echo "FIXMEs: $(grep -r "FIXME" src/ api_server.py | wc -l)"
echo "HACKs: $(grep -r -i "hack\|workaround" src/ | wc -l)"
echo "Version notes: $(grep -r "v[0-9]\." src/ *.py | wc -l)"
echo "Magic numbers: $(grep -r "[0-9]\{2,\}.*#" src/ *.py | wc -l)"
echo "Frustrated notes: $(grep -r -i "ugh\|damn\|weird\|dumb" src/ | wc -l)"
echo "Old code: $(grep -r "^[ ]*#.*old\|deprecated" src/ | wc -l)"

TOTAL=$(grep -r "TODO\|FIXME\|hack\|v[0-9]\.\|ugh" src/ *.py 2>/dev/null | wc -l)
echo ""
if [ $TOTAL -gt 30 ]; then
    echo "✅ Humanization PASSED (Score: $TOTAL)"
else
    echo "❌ Too clean! (Score: $TOTAL < 30)"
fi