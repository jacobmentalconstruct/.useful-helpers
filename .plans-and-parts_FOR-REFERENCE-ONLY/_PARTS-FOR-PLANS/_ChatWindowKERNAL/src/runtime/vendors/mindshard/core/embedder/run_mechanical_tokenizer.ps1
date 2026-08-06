param(
    [string]$Text = "",
    [string]$Path = "",
    [int]$NearestK = 8,
    [int]$MaxChars = 4000
)

$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$toolPath = Join-Path $bundleRoot "inspect_text.py"

if (-not $Text -and -not $Path) {
    Write-Error "Provide -Text or -Path."
    exit 2
}

$argsMap = @{
    nearest_k = [string]$NearestK
    max_chars = [string]$MaxChars
}

if ($Path) {
    $argsMap.path = $Path
} else {
    $argsMap.text = $Text
}

$argsJson = $argsMap | ConvertTo-Json -Compress
& python -B $toolPath --args-json $argsJson
exit $LASTEXITCODE
