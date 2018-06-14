# Script to analyse the data

# First step parameters
param (
    [Parameter(Mandatory=$false)][string]$signsrch,
    [Parameter(Mandatory=$false)][string]$strings,
    [Parameter(Mandatory=$true)][string]$sourcepath
)

# If signsrch is not defined, put a default one
if (!$signsrch) {

    $signsrch = "res\signsrch.exe"
}

# If strings path is not defined, put a default one
if (!$strings) {

    $strings = "res\strings64.exe"
}

# logpath is  always root + name
$Global:logpath = "analysis_script_log.txt"

# If logpath already exists, clear the file's content
if(Test-Path -LiteralPath $logpath) {

    Clear-Content -LiteralPath $logpath
}

# results path - path to where results are stored
$Global:resultspath = "results"
# path to signatures file - where results are stored
$Global:signaturesfile = "analysis_signatures.dat"

# Other variables

# Stores the number of binaries in which at least one signature has been found
$Global:numberofbinarieswithsign = 0
# Total number of binaries that have been evaluated
$Global:numberofbinaries = 0
# Hash that holds signature id and an array of files where that signature has been found
$Global:signatures_hash = @{}
# Array that holds signature object at the underlying id
$Global:signatures_array = @()

# Function to log messages
function Log-Message([string]$message) {

    $message | Add-Content -LiteralPath $logpath
}

# Function to quickly create a signature object
function Create-Signature-Object([int]$id, [string]$description, [string]$bitsendiansize) {
    
    $object = New-Object –TypeName PSObject
    $object | Add-Member –MemberType NoteProperty –Name SignatureID –Value $id
    $object | Add-Member –MemberType NoteProperty –Name SignatureDescription –Value $description
    $object | Add-Member –MemberType NoteProperty –Name SignatureBitsEndianSize –Value $bitsendiansize
    $object | Add-Member -MemberType ScriptMethod -Name ToString {"$($this.SignatureID) $($this.SignatureDescription) $($this.SignatureBitsEndianSize)"} -Force
    $object
}

# Function to list signatures and build the hash for each signature
function List-Signatures() {

    # Call the list command of binsrch and output it to a .dat file
    if(Test-Path -LiteralPath $signaturesfile) {

        Clear-Content -LiteralPath $signaturesfile
    }
    $content = &$signsrch "-l" 2>$null
    foreach($line in ($content | Select -Skip 6)) {
    
        if ($line | Select-String -Pattern "^\s{2}[\d]{1,4}\s{1,4}(\w+|\W+)+(\]$)") {
            
            # Create the new object
            $aux_signature_object = Create-Signature-Object (($line | Select-String -Pattern "\d{1,4}").Matches.Value) (($line | Select-String -Pattern "\b\s{1,4}(\w|\W)+\[").Matches.Value -replace "^\s|\s\[", "") (($line | Select-String -Pattern "\[(\w+|\W+)+\]").Matches.Value)

            # First add the object to the signatures array
            $Global:signatures_array += $aux_signature_object

            # Add to the hash the signature that matches the pattern with one whitespace
            # instead of double whitespace and an empty array
            $Global:signatures_hash.Add($aux_signature_object.SignatureID, @())
        }
    }
}

function Search-Binaries() {

    Write-Output "----------------------------------------------"
    Log-Message("----------------------------------------------")
    Write-Output("[INFO]: STEP 1 - creating reports with signsrch")
    Log-Message("[INFO]: STEP 1 - creating reports with signsrch")
    # Go through bins
    $binaries = Get-ChildItem $binspath -Include *.bin -Recurse -ErrorAction SilentlyContinue | Where { ($_.Attributes -eq -1) -or (!$_.PSIsContainer) }
    foreach($binary in $binaries) {
        $error.clear()
        try {
        
            Write-Output "[INFO]: Analysing $($binary.FullName) ..."
            Log-Message("[INFO]: Analysing $($binary.FullName) ...")
            if(Test-Path (Join-Path -Path $binary.DirectoryName -ChildPath ($binary.Name + ".signdat"))) {

                Clear-Content (Join-Path -Path $binary.DirectoryName -ChildPath ($binary.Name + ".signdat"))
            }
            &$signsrch $binary.FullName 2>$null| Add-Content -LiteralPath (Join-Path -Path $binary.DirectoryName -ChildPath ($binary.Name + ".signdat"))
        } catch {

            Write-Error "[ERROR]: An error occurred - $error"
            Log-Message("[ERROR]: An error occurred - $error")
        }
    }

    Write-Output("[INFO]: STEP 1 COMPLETED")
    Log-Message("[INFO]: STEP 1 COMPLETED")
}

function Analyse-Reports() {

    Write-Output "----------------------------------------------"
    Log-Message("----------------------------------------------")
    Write-Output("[INFO]: STEP 2 - analysing reports")
    Log-Message("[INFO]: STEP 2 - analysing reports")
    $reportsdata = Get-ChildItem $binspath -Include *.signdat -Recurse -ErrorAction SilentlyContinue
    $Global:numberofbinaries = ($reportsdata | Measure-Object).Count
    foreach($reportdata in $reportsdata) {
        $error.clear()
        try {
            Write-Output "[INFO]: Analysing $($reportdata.FullName) ..."
            Log-Message "[INFO]: Analysing $($reportdata.FullName) ..."
            $reportcontent = Get-Content -LiteralPath $reportdata.FullName
            if(($reportcontent | Measure-Object).Count -gt 12) {
                
                $Global:numberofbinarieswithsign = ($Global:numberofbinarieswithsign + 1)

                $binarypath = ($reportcontent[0] | Select-String -Pattern '(\"(\w+|\W+)+\")').Matches.Value.Replace('"',"") 

                $datastrings = ""
                &$strings "-nobanner" $binarypath 2>$null| Select-String -Pattern "^(?=\d)(?:(?:31(?!.(?:0?[2469]|11))|(?:30|29)(?!.0?2)|29(?=.0?2.(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00)))(?:\x20|$))|(?:2[0-8]|1\d|0?[1-9]))([-.\/])(?:1[012]|0?[1-9])\1(?:1[6-9]|[2-9]\d)?\d\d(?:(?=\x20\d)\x20|$))?(((0?[1-9]|1[012])(:[0-5]\d){0,2}(\x20[AP]M))|([01]\d|2[0-3])(:[0-5]\d){1,2})?$" | ForEach-Object {
                    
                    $datastrings = $datastrings + " " + $_.ToString()
                }

                foreach($line in ($reportcontent | Select -Skip 10 | Select -SkipLast 2)) {
                    
                    if($line | Select-String -Pattern "\s{1}[\d]{1,4}\s{1,4}(\w+|\W+)+(\]$)") {

                        $regexed_line = ($line | Select-String -Pattern "\s{1}[\d]{1,4}\s{1,4}(\w+|\W+)+(\]$)").Matches.Value
                        # If the line matches our regex, take the value at the line key and add the document name in it
                        if($datastrings -eq "") {

                            $Global:signatures_hash[[int](($regexed_line | Select-String -Pattern "\d{1,4}").Matches.Value) - 1] += $binarypath
                        } else {
                        
                            $Global:signatures_hash[[int](($regexed_line | Select-String -Pattern "\d{1,4}").Matches.Value) - 1] += $binarypath + " ----------------->DATE=" + $datastrings
                        }
                    }
                }
            }
             
        } catch {
            
            Write-Error "[ERROR]: An error occurred - $error"
            Log-Message("[ERROR]: An error occurred - $error")
        }
    }
    Write-Output("[INFO]: STEP 2 COMPLETED")
    Log-Message("[INFO]: STEP 2 COMPLETED")
}

if(!(Test-Path -LiteralPath $signsrch)) {

    Write-Error "[ERROR]: $signsrch path does not exist"
    Log-Message("[ERROR]: $signsrch path does not exist")
    exit(1)
}

if(!(Test-Path -LiteralPath $strings)) {
    
    Write-Error "[ERROR]: $strings path does not exist"
    Log-Message("[ERROR]: $strings path does not exist")
    exit(1)
}

if(!(Test-Path -LiteralPath $sourcepath)) {
    
    Write-Error "[ERROR]: $sourcepath path does not exist"
    Log-Message("[ERROR]: $sourcepath path does not exist")
    exit(1)
}

# Create the results path
if(!(Test-Path -LiteralPath $resultspath)) {

    New-Item -ItemType directory -Path $resultspath >$null
}

List-Signatures

Search-Binaries

Analyse-Reports

Write-Output "----------------------------------------------"
if(Test-Path (Join-Path -Path $resultspath -ChildPath "signsrch_results.dat")) {

    Clear-Content (Join-Path -Path $resultspath -ChildPath "signsrch_results.dat")
}
Write-Output "Number of binaries: $Global:numberofbinaries"
"Number of binaries: $Global:numberofbinaries" | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "signsrch_results.dat")
Write-Output "Number of binaries with signatures: $Global:numberofbinarieswithsign"
"Number of binaries with signatures: $Global:numberofbinarieswithsign`n" | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "signsrch_results.dat")
foreach ($h in ($Global:signatures_hash.GetEnumerator() | Sort-Object Name)) {

    if($h.Value.Count -ne 0) {
    
        Write-Output "$($signatures_array[$($h.Name)]): $($h.Value.Count)"
        "$($signatures_array[$($h.Name)]): $($h.Value.Count)`n" | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "signsrch_results.dat")
    }
}
foreach ($h in ($Global:signatures_hash.GetEnumerator() | Sort-Object Name)) {

    if($h.Value.Count -ne 0) {
    
        "$($signatures_array[$($h.Name)])" | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "signsrch_results.dat")
        foreach($iterator in $($h.Value)) {
            $iterator | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "signsrch_results.dat")
        }
        "`n" | Add-Content -LiteralPath (Join-Path -Path $resultspath -ChildPath "signsrch_results.dat")
    }
}
Write-Output "[INFO]: Done!"
Log-Message("[INFO]: Done!")