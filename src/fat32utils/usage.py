help_str = '''
Usage:
python -m fat32utils <command> [options] <file>

Commands:
    delete     Mark a file as deleted in the filesystem
    undelete   Restore a file marked as deleted
    repoint    Points the file to another cluster
    hide       Hides a file by repointing it, but stores data in the new cluster to make
               it restorable
    restore    Restore a file hidden with the 'hide' command
    help       Show this help

Options:
    These options are only valid for the 'repoint' command
    --to-cluster <num>  The cluster the file should point to (default 0)
    --size <num>        The size the file should be marked to have (default 0)
'''
def print_usage():
  print(help_str)