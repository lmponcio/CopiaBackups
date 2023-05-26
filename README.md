# copia-backups

A script for creating backups of multiple folders/files into multiple destinations.

## Watch it work

In this example video I use copia backups for saving timestamped backups in a USB Drive and other destinatinos.

[![Watch Video](https://img.youtube.com/vi/CtHMa4s8YBw/0.jpg)](https://www.youtube.com/watch?v=CtHMa4s8YBw)

## How to use it

- **Definitions**:
    - Backup routine: we call backup routine to the process of copying the files and folders stated in a list of source paths into destinations stated in a list of destination paths. The backup routines are manually configured in "routines.json" before running the script - to add a new backup routine it is necessary to provide three things: a routine name, a list of sources, and a list of destinations. The "routines.json" file can contain as many routines as needed - each routine must have a different name.
    - Source paths: these are paths that we want to create a backup of. They can be paths of folders (so all subfolders & files will be copied) or paths of files (when only wanting to save one file). The list of source paths in a routine can contain as many source paths as needed.
    - Destination paths: these are the paths where we want to save our backups. They must to be folders (a file can't be a destination path). The list of destination paths in a routine can contain as many destinations paths as needed.

- **How-to**:
	- The file "routines.json" is used as an input by the script. In this json file all the routines are stated; because of this the user has to manually add the routines that wants to run in here before running the script (once you add a routine once, you can run it as many times as you want without opening the json file again). The file "routines.json" must be in the same folder as "main.py" for the script to find the routines.
	- The script runs by executing the file "main.py" and providing the positional and optional arguments as needed.
		- **Positional arguments**: at least the name of one routine must be provided. All the routines given as positional arguments will be run.
			- Example: running one routine
				```
				python main.py "example_routine"
				```
				In the case shown above the routine called 'example_routine' is run.
			- Example: running more than one routine
				```
				python main.py "example_routine1" "example_routine2"
				```
				In the case shown above the routines 'example_routine1' and 'example_routine2' are  run.
		-	**Optional arguments**: with them you can choose for the backups to be zipped (by default files are copied), for the timestamps not to be added (by default timestamp prefixes are aded), and for the existence of the backups to be checked at the end of the process (by default no verification is performed). Summary table and examples below:
			- Summary table:
			
				Optional Argument | Action
				-------------------|--------------
				-c | zip the backup (compress)
				-t | no timestamp prefix (keep src name of file/folder)
				-v | verify files at the end (make sure dst files/folders exist)
			
			-	Example: compressing with "-c"
				```
				python main.py "example_routine" -c
				```
				In the case shown above the routine called 'example_routine' is run and the backups are zipped.
			- Example: removing timestamp prefix with ""-t"
				```
				python main.py "example_routine" -c -t
				```
				In the case shown above the routine called 'example_routine' is run, the backups are zipped and timestamp prefixes are not added.					
			- Example: verifying backups were created at the end of the process with "-v"
				```
				python main.py "example_routine" -v
				```
				In the case shown above the routine called 'example_routine' is run and a verification process is performed at the end of the run. The results of this verification process can be seen in the log.
