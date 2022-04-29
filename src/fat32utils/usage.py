help_str = '''
Usage:
fat32utils <command> [options] <file>

Commands:
    info            Show filesystem information about a file
    delete          Mark a file as deleted in the filesystem
    undelete        Restore a file marked as deleted
    repoint         Points the file to another cluster
    hide            Hides a file by repointing it, but stores data in the new cluster to make
                    it restorable
    restore         Restore a file hidden with the 'hide' command
    settime         Set the create, access and/or modify timestamps for a file
    help [command]  Show this help, or help for a specific command
'''
help_info = '''
Show filesystem information about a file

Usage:
fat32utils info <file>

Information diplayed:
Name, DOS short name, Attributes, Create time, Last access date, Modify time,
Reserved clusters, Size, Location of file entry (sector + byte offset)
'''

help_hide = '''
Hides a file by repointing it, but stores data in the new cluster to make it restorable

Usage:
fat32utils hide <file>
'''
help_restore = '''
Restore a file hidden with the 'hide' command

Usage:
fat32utils restore <file>
'''

help_delete = '''
Mark a file as deleted in the filesystem, but retains cluster allocation

Usage:
fat32utils delete <file>
'''

help_undelete = '''
Restore a file marked as deleted

Usage:
fat32utils undelete <file>
'''

help_repoint = '''
Restore a file marked as deleted

Usage:
fat32utils repoint [options] <file>

Options:
    --to-cluster <num>  The cluster the file should point to (default 0)
    --size <num>        The size the file should be marked to have (default 0)
'''
help_settime = '''
Set the create, access and/or modify timestamps for a file

Usage:
fat32utils settime <options> <file>

Options:
    --ctime <timestamp> Create time
    --atime <timestamp> Access time
    --mtime <timestamp> Modify time

Timestamps should be in ISO 8601 format (yyyy-mm-dd hh:mm:ss.sss), and at least the date part need
to be specified (the rest of the values are then set to 0). Note that FAT32 only stores the date for 
access time, modify time is stored with 2 second presicion, and create time with 10 ms presicion.
'''

COMMAND_HELP = { 'hide': help_hide,
                 'restore': help_restore,
                 'delete': help_delete,
                 'undelete': help_undelete,
                 'repoint': help_repoint }

def print_usage(**kwargs):
  if kwargs.get('command', None) in COMMAND_HELP:
    print(COMMAND_HELP[kwargs['command']])
  else:
    print(help_str)