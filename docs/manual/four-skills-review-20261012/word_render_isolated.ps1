param(
  [Parameter(Mandatory = $true)][string]$InputDoc,
  [Parameter(Mandatory = $true)][string]$PdfPath,
  [string]$TextPath,
  [string]$ReportPath,
  [switch]$UpdateAndSave,
  [string]$WorkRoot = ''
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($WorkRoot)) { $WorkRoot = $PSScriptRoot }
if ([string]::IsNullOrWhiteSpace($WorkRoot)) {
  $WorkRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$resolvedRoot = [System.IO.Path]::GetFullPath($WorkRoot).TrimEnd('\')
function Assert-WorkPath([string]$Candidate, [bool]$MustExist) {
  $full = [System.IO.Path]::GetFullPath($Candidate)
  if (-not $full.StartsWith($resolvedRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Only files inside the task staging/work directory may be used: $full"
  }
  if ($MustExist -and -not [System.IO.File]::Exists($full)) { throw "File not found: $full" }
  return $full
}
$InputDoc = Assert-WorkPath $InputDoc $true
$PdfPath = Assert-WorkPath $PdfPath $false
if ($TextPath) { $TextPath = Assert-WorkPath $TextPath $false }
if (-not $ReportPath) { $ReportPath = Join-Path $resolvedRoot 'word_render_result.json' }
$ReportPath = Assert-WorkPath $ReportPath $false
if ($UpdateAndSave -and ([System.IO.Path]::GetFileName($InputDoc) -eq 'before.docx')) {
  throw 'The before.docx baseline must not be modified. Use an authored staging copy.'
}
foreach ($target in @($PdfPath, $TextPath, $ReportPath)) {
  if ($target) { [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($target)) }
}
if (-not ('TaskManualWordWindow' -as [type])) {
  Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class TaskManualWordWindow {
  [DllImport("user32.dll")]
  public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
}
'@
}
function Get-ApplicationProcessId($Application) {
  $window = [IntPtr]([Int64]$Application.Hwnd)
  # An empty invisible Word application can legitimately have no window yet.
  if ($window -eq [IntPtr]::Zero) { return 0 }
  [uint32]$applicationProcessId = 0
  [void][TaskManualWordWindow]::GetWindowThreadProcessId($window, [ref]$applicationProcessId)
  if ($applicationProcessId -eq 0) { throw 'The COM window could not be mapped to a process.' }
  return [int]$applicationProcessId
}
function Test-SameComIdentity($First, $Second) {
  $firstIdentity = [IntPtr]::Zero
  $secondIdentity = [IntPtr]::Zero
  try {
    $firstIdentity = [System.Runtime.InteropServices.Marshal]::GetIUnknownForObject($First)
    $secondIdentity = [System.Runtime.InteropServices.Marshal]::GetIUnknownForObject($Second)
    return ($firstIdentity -eq $secondIdentity)
  } finally {
    if ($firstIdentity -ne [IntPtr]::Zero) { [void][System.Runtime.InteropServices.Marshal]::Release($firstIdentity) }
    if ($secondIdentity -ne [IntPtr]::Zero) { [void][System.Runtime.InteropServices.Marshal]::Release($secondIdentity) }
  }
}
function Test-OwnedApplication($Application) {
  if (-not $ownedInstance -or ($initialWordIds -contains $ownedWordId)) { return $false }
  if (-not (Test-SameComIdentity $Application $wordApp)) { return $false }
  $ownedProcess = Get-Process -Id $ownedWordId -ErrorAction SilentlyContinue
  if (-not $ownedProcess -or $ownedProcess.ProcessName -ne 'WINWORD') { return $false }
  if ($ownedProcess.StartTime.ToUniversalTime().Ticks -ne $ownedStartTicks) { return $false }
  $mappedId = Get-ApplicationProcessId $Application
  if ($mappedId -ne 0) { return ($mappedId -eq $ownedWordId) }
  # If Word remains windowless, require the same COM identity plus the one
  # independently created PID and its unchanged process creation timestamp.
  return $true
}
$initialWordIds = @(Get-Process WINWORD -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
$wordApp = $null
$openedDocument = $null
$ownedInstance = $false
$ownedWordId = 0
$ownedStartTicks = 0L
$failure = $null
$cleanupWarnings = [System.Collections.Generic.List[string]]::new()
$result = [ordered]@{
  input = $InputDoc; pdf = $PdfPath; text = $TextPath
  update_and_save = $UpdateAndSave.IsPresent
  initial_word_pids = $initialWordIds; owned_word_pid = $null
  ownership_verified = $false; pages = $null; status = 'not_started'
  ownership_method = $null; hwnd_pid_before_open = $null; hwnd_pid_after_open = $null
  user_instances_touched = $false
}
try {
  $wordApp = New-Object -ComObject Word.Application
  $newWordProcesses = @(Get-Process WINWORD -ErrorAction SilentlyContinue | Where-Object { $initialWordIds -notcontains $_.Id })
  if (($newWordProcesses.Count -ne 1) -or ($wordApp.Documents.Count -ne 0)) {
    throw 'Word did not supply a new empty instance. No existing user document was opened, changed or closed.'
  }
  $candidateId = $newWordProcesses[0].Id
  $mappedBefore = Get-ApplicationProcessId $wordApp
  $result.hwnd_pid_before_open = $mappedBefore
  if (($mappedBefore -ne 0) -and ($mappedBefore -ne $candidateId)) {
    throw 'The COM window does not belong to the single newly created Word process.'
  }
  $ownedInstance = $true
  $ownedWordId = $candidateId
  $ownedStartTicks = $newWordProcesses[0].StartTime.ToUniversalTime().Ticks
  $result.owned_word_pid = $ownedWordId
  $result.ownership_verified = $true
  $result.ownership_method = 'single_new_pid_and_empty_COM_instance'
  $wordApp.Visible = $false
  $wordApp.DisplayAlerts = 0
  $wordApp.AutomationSecurity = 3
  $wordApp.Options.UpdateLinksAtOpen = $false
  $openedDocument = $wordApp.Documents.Open($InputDoc, $false, (-not $UpdateAndSave.IsPresent), $false)
  if (-not (Test-OwnedApplication $openedDocument.Application)) {
    throw 'The opened staging document belongs to an unexpected Word instance.'
  }
  $mappedAfter = Get-ApplicationProcessId $openedDocument.Application
  $result.hwnd_pid_after_open = $mappedAfter
  if ($mappedAfter -ne 0) {
    $result.ownership_method = 'single_new_pid_COM_identity_and_verified_hwnd'
  } else {
    $result.ownership_method = 'single_new_pid_creation_time_and_COM_identity_hwnd_zero'
  }
  if (-not ([System.IO.Path]::GetFullPath($openedDocument.FullName)).Equals($InputDoc, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Word opened a different path than the requested staging document.'
  }
  if ($UpdateAndSave) {
    if ($openedDocument.ReadOnly) { throw 'The staging document opened read-only; it was not saved.' }
    [void]$openedDocument.Fields.Update()
    foreach ($toc in $openedDocument.TablesOfContents) {
      try { $toc.Update() } finally { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($toc) }
    }
    $openedDocument.Repaginate()
    foreach ($toc in $openedDocument.TablesOfContents) {
      try { $toc.UpdatePageNumbers() } finally { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($toc) }
    }
    $openedDocument.Save()
  }
  $openedDocument.Repaginate()
  if ($TextPath) {
    [System.IO.File]::WriteAllText($TextPath, $openedDocument.Content.Text, [System.Text.UTF8Encoding]::new($false))
  }
  $openedDocument.ExportAsFixedFormat($PdfPath, 17)
  if (-not ([System.IO.File]::Exists($PdfPath)) -or ((Get-Item -LiteralPath $PdfPath).Length -eq 0)) {
    throw 'Word did not produce a nonempty PDF.'
  }
  $result.pages = $openedDocument.ComputeStatistics(2)
  $result.status = 'success'
} catch {
  $failure = $_
  $result.status = 'failed'
  $result.error = $_.Exception.Message
} finally {
  if ($openedDocument) {
    try {
      if (Test-OwnedApplication $openedDocument.Application) {
        $openedDocument.Close(0)
      } else { $cleanupWarnings.Add('Document Close skipped because instance ownership could not be verified.') }
    } catch { $cleanupWarnings.Add('Staging document cleanup: ' + $_.Exception.Message) }
    try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($openedDocument) } catch {}
    $openedDocument = $null
  }
  if ($wordApp) {
    try {
      if (Test-OwnedApplication $wordApp) {
        if ($wordApp.Documents.Count -eq 0) {
          [object]$quitWithoutSaving = 0
          $wordApp.Quit([ref]$quitWithoutSaving)
        }
        else { $cleanupWarnings.Add('Word Quit skipped: additional documents appeared in the owned instance.') }
      }
    } catch { $cleanupWarnings.Add('Owned Word cleanup: ' + $_.Exception.Message) }
    try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp) } catch {}
  }
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
  $result.cleanup_warnings = @($cleanupWarnings.ToArray())
  $result.finished_at = (Get-Date).ToString('o')
  [System.IO.File]::WriteAllText($ReportPath, ($result | ConvertTo-Json -Depth 5), [System.Text.UTF8Encoding]::new($false))
}
$result | ConvertTo-Json -Depth 5
if ($failure) { throw $failure }
