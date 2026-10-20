# Run from an Cloud checkout or downloaded release archive.
& python (Join-Path $PSScriptRoot 'deploy.py') install @args
exit $LASTEXITCODE
