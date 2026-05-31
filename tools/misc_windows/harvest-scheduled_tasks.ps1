# Initialize the Task Service COM object to access deep task properties
$taskService = New-Object -ComObject Schedule.Service
$taskService.Connect()

# Helper function to recursively get all tasks from all folders
function Get-AllTasks ($folder) {
    $tasks = @()
    try {
        $tasks += $folder.GetTasks(0)
    } catch {
        Write-Warning "Could not retrieve tasks from folder: $($folder.Path)"
    }

    foreach ($subFolder in $folder.GetFolders(0)) {
        $tasks += Get-AllTasks $subFolder
    }
    return $tasks
}

# Helper function to convert any DateTime to UTC ISO 8601 string safely
function Format-ToUtcIso ($dateTimeValue) {
    if ($null -eq $dateTimeValue) { return $null }

    if ($dateTimeValue -is [DateTime]) {
        if ($dateTimeValue.Year -le 1900) { return $null }
        return $dateTimeValue.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }

    $parsedDate = $null
    if ([DateTime]::TryParse($dateTimeValue, [ref]$parsedDate)) {
        if ($parsedDate.Year -le 1900) { return $null }
        return $parsedDate.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }

    return $dateTimeValue
}

# Start from the root folder
$rootFolder = $taskService.GetFolder("\")
$allTasks = Get-AllTasks $rootFolder

# Dynamic identification of your current terminal directory path
$currentDir = $ExecutionContext.SessionState.Path.CurrentFileSystemLocation.Path
$outputPath = Join-Path -Path $currentDir -ChildPath "scheduled_tasks_harvest.json"

# Clear file if it already exists to prevent appending to old data
if (Test-Path $outputPath) { Remove-Item $outputPath }

$totalTasksCount = 0

foreach ($task in $allTasks) {
    $totalTasksCount++

    # Extract Definition and Properties safely
    $definition = $task.Definition
    $registrationInfo = $definition.RegistrationInfo
    $settings = $definition.Settings
    $principal = $definition.Principal

    # 1. Capture and Process Actions
    $actions = @()
    if ($null -ne $definition.Actions) {
        $actions = foreach ($action in $definition.Actions) {
            $actionType = $action.Type
            $actionData = [ordered]@{
                type = if ($null -ne $actionType) { $actionType.ToString() } else { $null }
            }

            # 0 = TASK_ACTION_EXEC
            if ($actionType -eq 0) {
                $path = $action.Path
                $arguments = $action.Arguments

                $directory = $null
                if (-not [string]::IsNullOrWhiteSpace($path) -and $path.Contains("\")) {
                    try {
                        $directory = Split-Path -Path $path -Parent
                    } catch {
                        $directory = $null
                    }
                }

                $actionData['path'] = $path
                $actionData['arguments'] = $arguments
                $actionData['directory'] = $directory
                $actionData['working_directory'] = $action.WorkingDirectory

                if (-not [string]::IsNullOrWhiteSpace($arguments)) {
                    $actionData['command_line'] = "$path $arguments"
                } else {
                    $actionData['command_line'] = $path
                }
            }
            # 5 = TASK_ACTION_COM_HANDLER
            elseif ($actionType -eq 5) {
                $actionData['class_id'] = $action.ClassId
                $actionData['data'] = $action.Data
                $actionData['command_line'] = "COM Handler: $($action.ClassId)"
            }
            # 6 = TASK_ACTION_SEND_EMAIL
            elseif ($actionType -eq 6) {
                $actionData['subject'] = $action.Subject
                $actionData['to'] = $action.To
                $actionData['cc'] = $action.Cc
                $actionData['bcc'] = $action.Bcc
                $actionData['reply_to'] = $action.ReplyTo
                $actionData['server'] = $action.Server
                $actionData['body'] = $action.Body
                $actionData['command_line'] = "Email to: $($action.To) | Subject: $($action.Subject)"
            }
            # 7 = TASK_ACTION_SHOW_MESSAGE
            elseif ($actionType -eq 7) {
                $actionData['title'] = $action.Title
                $actionData['message_body'] = $action.MessageBody
                $actionData['command_line'] = "Show Message: $($action.Title)"
            }

            [PSCustomObject]$actionData
        }
    }

    # 2. Capture Triggers
    $triggers = @()
    if ($null -ne $definition.Triggers) {
        $triggers = foreach ($trigger in $definition.Triggers) {
            [ordered]@{
                type                 = if ($null -ne $trigger.Type) { $trigger.Type.ToString() } else { $null }
                enabled              = $trigger.Enabled
                start_boundary       = Format-ToUtcIso $trigger.StartBoundary
                end_boundary         = Format-ToUtcIso $trigger.EndBoundary
                id                   = $trigger.Id
                repetition           = if ($null -ne $trigger.Repetition) {
                    @{
                        interval             = $trigger.Repetition.Interval
                        duration             = $trigger.Repetition.Duration
                        stop_at_duration_end = $trigger.Repetition.StopAtDurationEnd
                    }
                } else { $null }
                execution_time_limit = $trigger.ExecutionTimeLimit
            }
        }
    }

    # 3. Process Principal and split domain/username if present
    $principalData = $null
    if ($null -ne $principal) {
        $domain = $null
        $username = $principal.UserId

        if (-not [string]::IsNullOrEmpty($principal.UserId) -and $principal.UserId.Contains("\")) {
            $splitUser = $principal.UserId -split '\\', 2
            $domain = $splitUser[0]
            $username = $splitUser[1]
        }

        $principalData = @{
            id            = $principal.Id
            user_id       = $principal.UserId
            domain        = $domain
            username      = $username
            logon_type    = if ($null -ne $principal.LogonType) { $principal.LogonType.ToString() } else { $null }
            group_id      = $principal.GroupId
            run_level     = if ($null -ne $principal.RunLevel) { $principal.RunLevel.ToString() } else { $null }
            display_name  = $principal.DisplayName
        }
    }

    # 4. Construct the Master Payload
    $taskPayload = [ordered]@{
        task_name             = $task.Name
        path                  = $task.Path
        enabled               = $task.Enabled
        state                 = switch ($task.State) {
            0 { "Unknown" }
            1 { "Disabled" }
            2 { "Queued" }
            3 { "Ready" }
            4 { "Running" }
            Default { "Unknown" }
        }
        last_run_time          = Format-ToUtcIso $task.LastRunTime
        last_task_result       = $task.LastTaskResult
        next_run_time          = Format-ToUtcIso $task.NextRunTime
        number_of_missed_runs  = $task.NumberOfMissedRuns
        xml                    = $task.Xml

        # Registration Info
        registration_info   = if ($null -ne $registrationInfo) {
            @{
                author              = $registrationInfo.Author
                description         = $registrationInfo.Description
                date                = Format-ToUtcIso $registrationInfo.Date
                documentation       = $registrationInfo.Documentation
                security_descriptor = $registrationInfo.SecurityDescriptor
                source              = $registrationInfo.Source
                version             = $registrationInfo.Version
            }
        } else { $null }

        # Principal / Security Context
        principal          = $principalData

        # Settings
        settings           = if ($null -ne $settings) {
            @{
                allow_start_if_on_batteries      = $settings.AllowStartIfOnBatteries
                allow_hard_terminate             = $settings.AllowHardTerminate
                compatibility                    = if ($null -ne $settings.Compatibility) { $settings.Compatibility.ToString() } else { $null }
                delete_expired_task_after        = $settings.DeleteExpiredTaskAfter
                disallow_start_if_on_batteries   = $settings.DisallowStartIfOnBatteries
                enabled                          = $settings.Enabled
                execution_time_limit             = $settings.ExecutionTimeLimit
                hidden                           = $settings.Hidden
                idle_settings                = if ($null -ne $settings.IdleSettings) {
                    @{
                        idle_duration      = $settings.IdleSettings.IdleDuration
                        wait_timeout       = $settings.IdleSettings.WaitTimeout
                        stop_on_idle_end   = $settings.IdleSettings.StopOnIdleEnd
                        restart_on_idle    = $settings.IdleSettings.RestartOnIdle
                    }
                } else { $null }
                multiple_instances_policy        = if ($null -ne $settings.MultipleInstancesPolicy) { $settings.MultipleInstancesPolicy.ToString() } else { $null }
                network_settings             = if ($null -ne $settings.NetworkSettings) {
                    @{
                        id   = $settings.NetworkSettings.Id
                        name = $settings.NetworkSettings.Name
                    }
                } else { $null }
                priority                     = $settings.Priority
                restart_count                = $settings.RestartCount
                restart_interval             = $settings.RestartInterval
                run_only_if_idle                 = $settings.RunOnlyIfIdle
                run_only_if_network_available    = $settings.RunOnlyIfNetworkAvailable
                start_when_available             = $settings.StartWhenAvailable
                stop_if_going_on_batteries       = $settings.StopIfGoingOnBatteries
                wake_to_run                      = $settings.WakeToRun
            }
        } else { $null }

        actions            = $actions
        triggers           = $triggers
    }

    # Generate compressed single-line JSON string
    $rawJsonLine = $taskPayload | ConvertTo-Json -Depth 10 -Compress

    # Strip inner escaped quotes if present
    $sanitizedJsonLine = $rawJsonLine -replace '(?<=: )"\\"([^"]+)\\""', '"$1"'

    # Print raw JSON directly to screen line-by-line
    Write-Output $sanitizedJsonLine

    # Write line out to log file
    $sanitizedJsonLine | Add-Content -Path $outputPath -Encoding utf8
}

# Print dynamic collection summary at the very end
Write-Host "`n--- HARVEST COMPLETE ---" -ForegroundColor Green
Write-Host "Total tasks collected: $totalTasksCount" -ForegroundColor Green
Write-Host "Log file saved directly to: " -NoNewline -ForegroundColor Cyan
Write-Host $outputPath -ForegroundColor Yellow
Write-Host "------------------------`n" -ForegroundColor Green
