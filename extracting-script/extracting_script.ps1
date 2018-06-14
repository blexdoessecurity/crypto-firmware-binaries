# Script to extract the data

# First step parameters
param (
    [Parameter(Mandatory=$false)][string]$winrar,
    [Parameter(Mandatory=$true)][string]$sourcepath
)

# If winrar is not defined, put a default one
if (!$winrar) {

    $winrar = "C:\Program Files (x86)\WinRAR\WinRAR.exe"
}

# logpath is  always root + name
$Global:logpath = "extracting_script_log.txt"

# If logpath already exists, clear the file's content
if(Test-Path -LiteralPath $logpath) {

    Clear-Content -LiteralPath $logpath
}

# path to binaries - where bins are extracted
$GLobal:binspath = "bins"

# Function to log messages
function Log-Message([string]$message) {

    $message | Add-Content -LiteralPath $logpath
}

# Copy all binaries from source to destination
function Copy-Binaries() {

    Write-Output "----------------------------------------------"
    Log-Message("----------------------------------------------")
    Write-Output("[INFO]: STEP 1 - copying existing binaries")
    Log-Message("[INFO]: STEP 1 - copying existing binaries")
    $binaries = Get-ChildItem $sourcepath -Include *.bin -Recurse | Where {($_.Attributes -eq -1) -or (!$_.PSIsContainer)}
    foreach($binary in $binaries) {
        $error.clear()
        try {
        
            Copy-Item ($binary.FullName) -Destination $binspath -Force

        } catch {

             Write-Error "[ERROR]: An error occurred - $error"
             Log-Message("[ERROR]: An error occurred - $error")
        }
    }
    Write-Output("[INFO]: STEP 1 COMPLETED")
    Log-Message("[INFO]: STEP 1 COMPLETED")
}

# Function to extract all the bins from archives stored in source to the destination
function Extract-Archives() {

    Write-Output "----------------------------------------------"
    Log-Message("----------------------------------------------")
    Write-Output("[INFO]: STEP 2 - extracting binaries")
    Log-Message("[INFO]: STEP 2 - extracting binaries")
    # Including all the extensions winrar can handle
    $archives = Get-ChildItem $sourcepath -Include *.rar, *.zip, *.cab, *.arj, *.lzh, *.lha, *.tar, *.gz, *.ace, *.jar, *.iso, *.7z, *.xz, *.z -Recurse | Where {($_.Attributes -eq -1) -or (!$_.PSIsContainer)}
    foreach ($archive in $archives) {
        $error.clear()
        try {
        
            Write-Output "[INFO]: Extracting $archive ..."
            Log-Message("[INFO]: Extracting $archive ...")
            &$winrar x -y -ad $archive.FullName *.bin ($binspath + "\") -p"password"
            Get-Process winrar | Wait-Process
        } catch {
            Write-Error "[ERROR]: An error occurred - $error"
            Log-Message("[ERROR]: An error occurred - $error")
        }
    }
    Write-Output("[INFO]: STEP 2 COMPLETED")
    Log-Message("[INFO]: STEP 2 COMPLETED")
}

if(!(Test-Path -LiteralPath $winrar)) {

    Write-Error "[ERROR]: $winrar path does not exist"
    Log-Message("[ERROR]: $winrar path does not exist")
    exit(1)
}

if(!(Test-Path -LiteralPath $sourcepath)) {
    
    Write-Error "[ERROR]: $sourcepath path does not exist"
    Log-Message("[ERROR]: $sourcepath path does not exist")
    exit(1)
}

# Create the bins path
if(!(Test-Path -LiteralPath $binspath)) {

    New-Item -ItemType directory -Path $binspath >$null
}

Copy-Binaries

Extract-Archives