CreateObject("WScript.Shell").Run "pythonw " & Chr(34) & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\downloader.py" & Chr(34), 0, False
