# replace-file-preserving-acls.ps1
# ----
# Moves/replaces a target file with a given source file,
# but only after copying ACLs from the targe file.
param (
	# The source file to move to the target
	[string]$from = "",
	# The destination to replace
	[string]$to = "",
	# The temporary location of the file to use when copy ACLs
	[string]$to_temp = ""
)

If (($from -eq '') -or ($to -eq '') -or ($to_temp -eq '')) {
    ""
    "ERROR: Missing argument(s)."

    # Pause for user
    ""
    "Press ENTER to cotinue."
    $Test=Read-Host
    exit 1
}


# Move-Item -Path "$from" "$to_temp"
Move-Item -Path "$from" "$to_temp"
Get-Acl -Path "$to" | Set-Acl -Path "$to_temp"
Move-Item -Force -Path "$to_temp" "$to"

"Updated [$to]"

# Pause for user
""
"Press ENTER to continue."
$Test=Read-Host
