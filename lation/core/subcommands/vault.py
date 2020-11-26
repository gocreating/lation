import click

from lation.core.command import cli
from lation.core.vault import Vault

@cli.group('vault')
@click.pass_context
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
def vault_cmd_group(ctx, password):
    vault = Vault(password)
    ctx.obj = vault

"""
Usage:
    python lation.py vault --password p encrypt --src s --dest d
"""
@vault_cmd_group.command('encrypt')
@click.pass_obj
@click.option('--src', required=True)
@click.option('--dest')
def vault_encrypt(vault, src, dest):
    vault.encrypt(src, dest=dest)

"""
Usage:
    python lation.py vault --password p decrypt --src s --dest d
"""
@vault_cmd_group.command('decrypt')
@click.pass_obj
@click.option('--src', required=True)
@click.option('--dest')
def vault_decrypt(vault, src, dest):
    try:
        vault.decrypt(src, dest=dest)
    except Exception as e:
        print(e)
