# Infuse database parser
This utility parses the Infuse SQLite database file and extracts information 
on movies, TV show seasons, and TV show episodes to more human-readable CSV files.

It assumes that you have a Mac with the Infuse app and this script installed on it.

## Database location
By default, it assumes that the database file is located at 
`~/Library/Containers/com.firecore.infuse/Data/Library/Application Support/Infuse/infuse.db`.

You can override this by setting the `--db_path` argument.

## Media format detection
This script will look at file names in order to determine if the media format they
are from, i.e. DVD/Bluray/UHD. Basically, it just looks for the strings `DVD`, 
`Bluray`, or `UHD` in the filename. Case does not matter. For movies, please 
be sure the `--share_path_prefix` is set as Infuse sometimes only stores the
folder name to a movie and not the full path with the file name. This seems to be 
the case when the folder only contains one movie file.

## Network share prefix (--share_path_prefix)
Infuse doesn't seem to store in the database the full local path, leaving out 
the mount point. For instance, Infuse will store `<share_name>/<movie_path>` 
but to access the file, it's actually `/Volume/<share_name>/<movie_path>`. There 
are script functions that require being able to access the actual files 
(e.g. media format detection). These are disabled if the script cannot access 
the files.

If you set `--share_path_prefix`, it will prefix that to the path names in the 
database.
