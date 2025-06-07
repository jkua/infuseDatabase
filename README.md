# Infuse database parser
This utility parses the Infuse SQLLite database file and extracts information 
on movies, TV show seasons, and TV show episodes to more human-readable CSV files.

It assumes that you have a Mac with the Infuse app and this script installed on it.

By default, it assumes that the database file is located at 
`~/Library/Containers/com.firecore.infuse/Data/Library/Application Support/Infuse/infuse.db`.

If you set `--share_path_prefix`, it will append that to the path names in the 
database in order to get the actual filenames for movies, as sometimes Infuse 
only stores the folder name. This is only used for the filename checked which
will look for `DVD`, `Bluray`, or `UHD` in the filename to indicate the media 
format the file was from.
