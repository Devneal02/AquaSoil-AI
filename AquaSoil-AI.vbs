Option Explicit

Dim shell, fso, projectDir, launcherPath, command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(fso.GetAbsolutePathName(WScript.ScriptFullName))
If Len(projectDir) = 0 Then
    projectDir = shell.CurrentDirectory
End If

launcherPath = fso.BuildPath(projectDir, "AquaSoil-AI.pyw")
If Not fso.FileExists(launcherPath) Then
    WScript.Echo "AquaSoil-AI could not find AquaSoil-AI.pyw. Keep this launcher in the project folder."
    WScript.Quit 1
End If

shell.CurrentDirectory = projectDir
command = "pyw -3 " & Quote(launcherPath)
shell.Run command, 0, False

Function Quote(value)
    Quote = Chr(34) & value & Chr(34)
End Function
