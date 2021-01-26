import click

@click.command()
@click.option("--exe", type=click.BOOL)
@click.option("--pyc", type=click.BOOL)
@click.option("--pyz")
@click.argument("code")
def main(exe, pyc, pyz, code):

