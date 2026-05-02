param(
    [switch]$FetchPolicySources
)

$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src;$env:PYTHONPATH"

$argsList = @()
if ($FetchPolicySources) {
    $argsList += "--fetch-policy-sources"
}
python -m gtd_capstone.pipelines.build_artifacts @argsList
