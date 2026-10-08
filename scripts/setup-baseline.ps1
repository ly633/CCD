param(
    [string]$GmpPrefix = 'C:/Users/ustc/anaconda3/Library',
    [string]$EigenConfigDir = 'C:/Users/ustc/anaconda3/envs/gdl_3dgs/Library/share/eigen3/cmake',
    [string]$BuildDirectory = 'build-baseline',
    [switch]$ConfigureOnly
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$results = Join-Path $repo 'baseline-results/setup'
New-Item -ItemType Directory -Force -Path $results | Out-Null

function Invoke-GitChecked {
    param([string[]]$Arguments)
    & git -c http.version=HTTP/1.1 -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=20 @Arguments
    if ($LASTEXITCODE -ne 0) { throw "git failed: $Arguments" }
}

# Fetch only the required revision. CPM's all-branch clones can stall on this network.
function Get-PinnedSource {
    param([string]$Name, [string]$Url, [string]$Revision)
    $destination = Join-Path $repo "external/baseline/$Name"
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    if (-not (Test-Path -LiteralPath (Join-Path $destination '.git'))) {
        Invoke-GitChecked -Arguments @('-C', $destination, 'init', '--quiet')
        Invoke-GitChecked -Arguments @('-C', $destination, 'remote', 'add', 'origin', $Url)
    }
    $remote = & git -C $destination remote get-url origin
    if ($remote -ne $Url) { throw "Unexpected remote in $destination" }
    $resolved = & git -C $destination rev-parse --verify "$Revision^{commit}" 2>$null
    $head = & git -C $destination rev-parse --verify HEAD 2>$null
    if (-not $resolved -or $head -ne $resolved) {
        Write-Host "Fetching $Name at $Revision"
        Invoke-GitChecked -Arguments @('-C', $destination, 'fetch', '--depth', '1', 'origin', $Revision)
        Invoke-GitChecked -Arguments @('-C', $destination, 'checkout', '--detach', 'FETCH_HEAD')
    }
    & git -C $destination diff --exit-code HEAD
    if ($LASTEXITCODE -ne 0) { throw "Dependency has local edits: $destination" }
}

Get-PinnedSource 'spdlog' 'https://github.com/gabime/spdlog.git' 'ad0e89cbfb4d0c1ce4d097e134eb7be67baebb36' # v1.11.0
Get-PinnedSource 'CCD-Query-IO' 'https://github.com/Continuous-Collision-Detection/CCD-Query-IO.git' 'efca80cda21d95d74a1477ed22d42db8aabb5835'
Get-PinnedSource 'pbar' 'https://github.com/estshorter/pbar.git' '226b9ad291d72c6859456d5188f33c932e2e730b'
Get-PinnedSource 'CLI11' 'https://github.com/CLIUtils/CLI11.git' '291c58789c031208f08f4f261a858b5b7083e8e2' # v2.3.2
& python (Join-Path $PSScriptRoot 'fetch-sample-data.py')
if ($LASTEXITCODE -ne 0) { throw 'Dataset preparation failed' }

$root = $repo.Replace('\', '/')
$arguments = @(
    '-S', $repo, '-B', $BuildDirectory, '-G', 'Visual Studio 17 2022', '-A', 'x64',
    '-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
    '-DCMAKE_CXX_FLAGS=/DWIN32 /D_WINDOWS /W3 /GR /EHsc /utf-8',
    '-DTIGHT_INCLUSION_WITH_SAMPLE_QUERIES=ON',
    '-DTIGHT_INCLUSION_WITH_DOUBLE_PRECISION=ON',
    '-DTIGHT_INCLUSION_WITH_TIMER=OFF',
    '-DTIGHT_INCLUSION_WITH_RATIONAL=OFF',
    '-DTIGHT_INCLUSION_LIMIT_QUEUE_SIZE=OFF',
    '-DTIGHT_INCLUSION_FLOAT_WITH_DOUBLE_INPUT=OFF',
    "-DCMAKE_PROJECT_TightInclusion_INCLUDE=$root/scripts/baseline-dependencies.cmake",
    "-DEigen3_DIR=$EigenConfigDir",
    "-DGMP_INCLUDES=$GmpPrefix/include",
    "-DGMP_LIBRARIES=$GmpPrefix/lib/gmp.lib",
    "-DGMP_RUNTIME_LIB=$GmpPrefix/bin/gmp.dll",
    "-DCPM_SOURCE_CACHE=$root/.cache/CPM",
    "-DCPM_spdlog_SOURCE=$root/external/baseline/spdlog",
    "-DCPM_CCD-Query-IO_SOURCE=$root/external/baseline/CCD-Query-IO",
    "-DCPM_pbar_SOURCE=$root/external/baseline/pbar",
    "-DCPM_CLI11_SOURCE=$root/external/baseline/CLI11",
    "-DCCD_IO_SAMPLE_QUERIES_DIR=$root/external/baseline/Sample-Queries-4d6cce3"
)
& cmake @arguments 2>&1 | Tee-Object -FilePath (Join-Path $results 'configure.log')
if ($LASTEXITCODE -ne 0) { throw 'CMake configure failed' }
if (-not $ConfigureOnly) {
    & cmake --build $BuildDirectory --config Release --parallel 8 2>&1 |
        Tee-Object -FilePath (Join-Path $results 'build.log')
    if ($LASTEXITCODE -ne 0) { throw 'CMake build failed' }
    Copy-Item -LiteralPath "$GmpPrefix/bin/gmp.dll" -Destination "$BuildDirectory/app/Release/gmp.dll"
}
