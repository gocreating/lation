import lation.core.subcommands
from lation.core.command import cli
from lation.core.module import load_modules

if __name__ == '__main__':
    load_modules()
    cli()
