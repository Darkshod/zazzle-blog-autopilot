# Registers a Windows 11 local scheduled task for 09:00 daily execution.
# Note: Local Windows Task Scheduler requires your PC to be awake; use GitHub Actions for 24/7 cloud scheduling.
$RepoPath = Split-Path -Parent $PSScriptRoot
$Action = New-ScheduledTaskAction -Execute "python" -Argument "-m zazzle_blog_autopilot.cli run-all" -WorkingDirectory $RepoPath
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
Register-ScheduledTask -TaskName "ZazzleBlogAutopilotDaily" -Action $Action -Trigger $Trigger -Description "Daily Zazzle Blog Autopilot run" -Force
Write-Host "Registered Windows Task: ZazzleBlogAutopilotDaily at 09:00 AM."
