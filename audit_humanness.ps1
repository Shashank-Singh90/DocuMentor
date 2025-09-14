Write-Host "=== DocuMentor Human Artifacts Audit ===" -ForegroundColor Cyan

$todos = (Get-ChildItem -Path src -Recurse -Filter *.py | Select-String "TODO" | Measure-Object).Count
$todos += (Select-String "TODO" api_server.py -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "TODOs: $todos"

$fixmes = (Get-ChildItem -Path src -Recurse -Filter *.py | Select-String "FIXME" | Measure-Object).Count
$fixmes += (Select-String "FIXME" api_server.py -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "FIXMEs: $fixmes"

$hacks = (Get-ChildItem -Path src -Recurse -Filter *.py | Select-String -Pattern "(hack|workaround)" -CaseSensitive:$false | Measure-Object).Count
Write-Host "HACKs: $hacks"

$versions = (Get-ChildItem -Path src -Recurse -Filter *.py | Select-String "v[0-9]\." | Measure-Object).Count
$versions += (Get-ChildItem -Path . -Filter *.py | Select-String "v[0-9]\." | Measure-Object).Count
Write-Host "Version notes: $versions"

$magic = (Get-ChildItem -Path src -Recurse -Filter *.py | Select-String "\d{2,}.*#" | Measure-Object).Count
$magic += (Get-ChildItem -Path . -Filter *.py | Select-String "\d{2,}.*#" | Measure-Object).Count
Write-Host "Magic numbers: $magic"

$frustrated = (Get-ChildItem -Path src -Recurse -Filter *.py | Select-String -Pattern "(ugh|damn|weird|dumb|stupid|wtf|sucks)" -CaseSensitive:$false | Measure-Object).Count
Write-Host "Frustrated notes: $frustrated"

$old = (Get-ChildItem -Path src -Recurse -Filter *.py | Select-String "^\s*#.*(old|deprecated|legacy|obsolete)" | Measure-Object).Count
Write-Host "Old code: $old"

$total = $todos + $fixmes + $hacks + $versions + $frustrated
Write-Host ""
if ($total -gt 30) {
    Write-Host "✅ Humanization PASSED (Score: $total)" -ForegroundColor Green
} else {
    Write-Host "❌ Too clean! (Score: $total < 30)" -ForegroundColor Red
}