$messtxt = "OS Verion : " + (Get-WmiObject -class Win32_OperatingSystem).Caption
(Get-WmiObject -class Win32_OperatingSystem).Caption | Out-File -FilePath $env:TEMP\osv.txt
$oReturn=[System.Windows.Forms.MessageBox]::Show($messtxt,"OS System Detecting",[System.Windows.Forms.MessageBoxButtons]::OKCancel)
 switch ($oReturn){
    "OK" {
        write-host "You pressed OK"
    }
    "Cancel" {
        write-host "You pressed Cancel"
    }
 }
