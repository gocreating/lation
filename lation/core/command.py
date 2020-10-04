import click

from lation.file_manager import FileManager

# https://github.com/pallets/click/issues/257#issuecomment-403312784
class Mutex(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if:list = kwargs.pop("not_required_if")

        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs["help"] = (kwargs.get("help", "") + "Option is mutually exclusive with " + ", ".join(self.not_required_if) + ".").strip()
        super(Mutex, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt:bool = self.name in opts
        for mutex_opt in self.not_required_if:
            if mutex_opt in opts:
                if current_opt:
                    raise click.UsageError("Illegal usage: '" + str(self.name) + "' is mutually exclusive with " + str(mutex_opt) + ".")
                else:
                    self.prompt = None
        return super(Mutex, self).handle_parse_result(ctx, opts, args)

@click.group()
def cli():
    pass

"""
Usage:
    python lation.py encrypt --src s --dest d --password p
"""
@cli.command('encrypt')
@click.option('--src')
@click.option('--dest')
@click.option('--password', prompt=True)
def encrypt(src, dest, password):
    file_manager = FileManager(source_path=src, destination_path=dest)
    file_manager.encrypt(password)

"""
Usage:
    python lation.py decrypt --src s --dest d --password p
"""
@cli.command('decrypt')
@click.option('--src')
@click.option('--dest')
@click.option('--password', prompt=True)
def decrypt(src, dest, password):
    file_manager = FileManager(source_path=src, destination_path=dest)
    file_manager.decrypt(password)
