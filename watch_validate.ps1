$ErrorActionPreference = "Stop"

param(
    # Pass a file to watch just that file. Pass a directory to watch all *.lov files.
    [Parameter(Mandatory = $true)]
    [string]$Path
)

function New-Watcher {
    param(
        [string]$WatchPath,
        [string]$Filter
    )
    $w = New-Object IO.FileSystemWatcher $WatchPath, $Filter
    $w.EnableRaisingEvents = $true
    $w.IncludeSubdirectories = $false
    return $w
}

function Run-Validate {
    param([string]$Target)
    Clear-Host
    Write-Host "Validating $Target`n"
    python run_validate.py $Target
}

if (Test-Path $Path -PathType Leaf) {
    $fullPath = (Resolve-Path $Path).Path
    $dir = Split-Path $fullPath
    $file = Split-Path $fullPath -Leaf
    Write-Host "Watching file: $fullPath"
    Write-Host "Press Ctrl+C to stop."
    $watcher = New-Watcher -WatchPath $dir -Filter $file

    Register-ObjectEvent $watcher Changed -SourceIdentifier "ValidateOnChange" -Action {
        Start-Sleep -Milliseconds 100
        Run-Validate -Target $fullPath
    } | Out-Null

    Run-Validate -Target $fullPath
}
elseif (Test-Path $Path -PathType Container) {
    $dir = (Resolve-Path $Path).Path
    Write-Host "Watching directory: $dir for *.lov changes"
    Write-Host "Press Ctrl+C to stop."
    $watcher = New-Watcher -WatchPath $dir -Filter "*.lov"

    Register-ObjectEvent $watcher Changed -SourceIdentifier "ValidateOnChange" -Action {
        Start-Sleep -Milliseconds 100
        $target = $Event.SourceEventArgs.FullPath
        Run-Validate -Target $target
    } | Out-Null
}
else {
    Write-Host "Path not found: $Path"
    exit 1
}

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Unregister-Event -SourceIdentifier "ValidateOnChange" -ErrorAction SilentlyContinue
    if ($watcher) { $watcher.Dispose() }
}
