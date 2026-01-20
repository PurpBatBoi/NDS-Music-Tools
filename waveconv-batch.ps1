Get-ChildItem -Filter *.wav | ForEach-Object {
    .\waveconv.exe -a $_.FullName -o "$($_.BaseName).swav" -v
}
