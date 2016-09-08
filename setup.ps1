#requires -version 3.0

# PowerShell Variables
$PSVersionMinimum = "3"
$PSVersionExpected = "5"
$PSVersionInstalled = $PSVersionTable.PSVersion.Major


# Functions

# Add-Path
function Add-Path() {
	[Cmdletbinding()]
	param([parameter(Mandatory=$True,ValueFromPipeline=$True,Position=0)][String[]]$AddedFolder)
	
	# Get the current search path from the environment keys in the registry.
	$OldPath=(Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment' -Name PATH).Path
	
	# See if a new folder has been supplied.
	if (!$AddedFolder) { Return 'No Folder Supplied. $ENV:PATH Unchanged `n' }
	
	# See if the new folder exists on the file system.
	if (!(TEST-PATH $AddedFolder)){ Return 'Folder Does not Exist, Cannot be added to $ENV:PATH `n' }cd
	
	# See if the new Folder is already in the path.
	if ($ENV:PATH | Select-String -SimpleMatch $AddedFolder){ Return 'Folder already within $ENV:PATH' }
	
	# Set the New Path
	$NewPath=$OldPath+';'+$AddedFolder
	Set-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment' -Name PATH -Value $newPath
}

	
# Check if is running with Admin rights
if (!([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")) {
	Write-Warning "You do not have Administrator rights to run this script!`nPlease re-run this script as an Administrator!"
	pause
	break
} else {
	
	# Check Execution Police
	$policy = Get-ExecutionPolicy -Scope Process
	if ($policy -ne "Unrestricted") {

		echo "`n[!] Execution Policy is: $policy`n"
		echo "[!] This script needs to change Execution Policy to run."
		echo "For more info: https://technet.microsoft.com/pt-br/library/ee176961.aspx"
		
		$setExecutionPolice = Read-Host "`n[?] Do you want to proceed? [Y] or [N]"
		# Change Execution Policy?
		if ($setExecutionPolice -eq "y" -Or $setExecutionPolice -eq "yes") {
			Set-ExecutionPolicy Unrestricted -Scope Process -Confirm
            Write-Host "You need to run this install script again"
		}
		else {
			echo "`nBefore running this install script, run this command with Admin rights: Set-ExecutionPolicy Unrestricted -Scope Process -Confirm"
			pause
			break
		}
	} else {
		
		# Check PowerShell version
		if ($PSVersionInstalled -ge $PSVersionMinimum) {
			# Start Install
			Write-Host "`nStarting HTTPie installation...`n"
			
			
			$chocoPath = $env:ChocolateyInstall
			$chocoExecutable = $chocoPath+"\bin\choco.exe"
			if (Test-Path $chocoExecutable) {
				# Chcolatey is already installed, proceed install
				
				# Install Python
				$pythonInstallExe = $chocoPath+"\lib\python3\tools\python.exe"
				if (Test-Path $pythonInstallExe) {
					# Already Installed
					
				} else {
					Write-Host "`n- Installing Python..."
					choco install python -y
				}				
				
				# Add to System Path
				Add-Path $chocoPath\lib\python3\tools\python.exe
				Add-Path $chocoPath\lib\python3\tools\Scripts
				
				# Install HTTPie
				Write-Host "`n- Installing requirements...`n"
				python -m pip install --upgrade pip setuptools
				
				Write-Host "`n- Installing HTTPie..."
				python -m pip install --upgrade httpie
				Add-Path $chocoPath\lib\python3\tools\Scripts\http.exe
				
				Write-Host "`n`n----- HTTPie Installed! -----`n"
				
			}
			else {
				# Chcolatey isn't installed, installing now...
				Write-Host "Chocolatey is needed to run this install script. `n Installing Chocolatey now..."
				(iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1')))>$null 2>&1
			}
			
		} else {
			#Prompt to update PowerShell
			echo "You need to update you PowerShell (your version is lower than 3) to run this script"
		}
	}
}