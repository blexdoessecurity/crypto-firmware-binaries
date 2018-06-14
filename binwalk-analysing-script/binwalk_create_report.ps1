# Script to produce a big report from the little report pieces

# First step parameters
param (
    [Parameter(Mandatory=$true)][string]$sourcepath
)
$resultspath = "results"

# Create the results path
if(!(Test-Path -LiteralPath $resultspath)) {

    New-Item -ItemType directory -Path $resultspath >$null
}

# If the report exists, rewrite the file
if(Test-Path (Join-Path -Path $resultspath -ChildPath "binwalk_results.dat")) {

    Clear-Content (Join-Path -Path $resultspath -ChildPath "binwalk_results.dat")
}

$binwalk_data = Get-ChildItem -Path $sourcepath -Include "*.walkdat" -Recurse

# Write the number of binaries to the results file
Write-Output "Number of binaries: $($binwalk_data.Count)"
"Number of binaries: $($binwalk_data.Count)" | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "binwalk_results.dat")

# Count the number of binaries with signatures
$count = 0
foreach($data in $binwalk_data) {

    try{
    
        # Get the contents of each binwalk report
        $content = Get-Content -LiteralPath $data.FullName
        if($content.Count -gt 8) { 
    
            $count = $count + 1
        }
    } catch {

        Write-Output "Error for $($data.FullName)"
        continue
    }
}

Write-Output "Number of binaries with signatures: $count"
"Number of binaries with signatures: $count" | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "binwalk_results.dat")

# Append the contents to the report
foreach($data in $binwalk_data) {

    try{
    
        # Get the contents of each binwalk report
        $content = Get-Content -LiteralPath $data.FullName
        if($content.Count -gt 8) { 
    
            $content | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "binwalk_results.dat")
        }
    } catch {

        Write-Output "Error for $($data.FullName)"
        continue
    }
}