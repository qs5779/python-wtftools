import click


@click.command()
@click.option("--as-cowboy", "-c", is_flag=True, help="Greet as a cowboy.")
@click.argument("name", default="world", required=False)
def main(name, as_cowboy):
    """Wtf tools provide base functionality for various automation and \
administration activities."""
    greet = "Howdy" if as_cowboy else "Hello"
    click.echo("{0}, {1}.".format(greet, name))
