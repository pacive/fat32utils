help_str = '''
Usage:
fat32utils <command> [options] <file>

Commands:
    delete          Mark a file as deleted in the filesystem
    undelete        Restore a file marked as deleted
    repoint         Points the file to another cluster
    hide            Hides a file by repointing it, but stores data in the new cluster to make
                    it restorable
    restore         Restore a file hidden with the 'hide' command
    help [command]  Show this help, or help for a specific command
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