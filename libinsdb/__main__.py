# -*- encoding: utf-8 -*-

from argparse import ArgumentParser
from cmd import Cmd
import os
from pathlib import Path
import subprocess
import sys
from uuid import UUID

from rich.console import Console
from rich.styled import Styled
from rich.table import Table
from rich.tree import Tree

from .objects import Entity, Quantity, Release  # noqa: F401
from .local import LocalInsDb
from .version import LIBINSDB_VERSION

PROMPT_CHARACTER = ">"

STYLES = {
    "entity": "cyan",
    "quantity": "white",
    "data_file": "bright_green",
    "error": "bold red",
    "uuid": "yellow",
}

DATETIME_FORMAT = "%Y-%m-%d"


def open_file(filename: Path | str) -> None:
    """Open a file with the application that was associated by the OS

    This is a portable version of Python’s `os.startfile()` function,
    which only works on Windows.
    """

    abs_path = Path(filename).absolute()

    if sys.platform == "win32":
        os.startfile(abs_path)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, abs_path])


def clean_uuid_from_hyphens(text: str) -> str:
    "Assuming that `text` is a UUID, remove any hyphen from it"
    return str(text).replace("-", "")


class ImoBrowser(Cmd):
    "Parse an IMo file"

    intro = f"""Welcome to Libinsdb shell version {LIBINSDB_VERSION}.

Type 'help' or '?' to list commands, 'quit' to exit.
"""

    selected_entity_uuid = None  # type: UUID | None

    def __init__(self, input_file_path, force_terminal):
        self.console = Console(highlight=False, force_terminal=force_terminal)
        super().__init__(stdout=self.console.file)

        self.imo = LocalInsDb(storage_path=input_file_path)
        self.update_prompt()

    def update_prompt(self):
        if self.selected_entity_uuid:
            entity = self.imo.query_entity(self.selected_entity_uuid)
            self.prompt = f"{entity.name}{PROMPT_CHARACTER} "
        else:
            self.prompt = f"{PROMPT_CHARACTER} "

    def child_entities(self, parent_entity_uuid: UUID | None = None) -> list[Entity]:
        "Return a list of the entities that are children of the selected one"

        if not parent_entity_uuid:
            parent_entity_uuid = self.selected_entity_uuid

        result = []  # typing: list[Entity]
        for cur_entity_uuid in self.imo.entities:
            cur_entity = self.imo.entities[cur_entity_uuid]
            if cur_entity.parent == parent_entity_uuid:
                result.append(cur_entity)

        return result

    def child_quantities(self, parent_entity_uuid: UUID | None = None) -> list[Quantity]:
        "Return a list of the quantities that are children of the selected entity"

        if not parent_entity_uuid:
            parent_entity_uuid = self.selected_entity_uuid

        if not parent_entity_uuid:
            return []

        selected_entity = self.imo.entities[parent_entity_uuid]
        return [self.imo.quantities[cur_uuid] for cur_uuid in selected_entity.quantities]

    def show_entity(self, uuid: UUID) -> None:
        entity = self.imo.entities[uuid]

        grid = Table.grid()
        grid.add_column(min_width=20)
        grid.add_column()

        grid.add_row("Entity name", Styled(entity.name, style=STYLES["entity"]))
        grid.add_row("UUID", Styled(str(entity.uuid), style=STYLES["uuid"]))
        grid.add_row("Full path", entity.full_path)
        grid.add_row("Parent UUID", Styled(str(entity.parent), style=STYLES["uuid"]))

        if entity.quantities:
            quantity_table = Table()
            quantity_table.add_column("UUID", style=STYLES["uuid"])
            quantity_table.add_column("Name")
            for cur_quantity_uuid in entity.quantities:
                cur_quantity = self.imo.quantities[cur_quantity_uuid]
                quantity_table.add_row(str(cur_quantity_uuid), cur_quantity.name)

            grid.add_row("Quantities", quantity_table)

        self.console.print(grid)

    def show_quantity(self, uuid: UUID) -> None:
        quantity = self.imo.quantities[uuid]

        grid = Table.grid()
        grid.add_column("UUID", min_width=25)
        grid.add_column("Name")

        grid.add_row("Quantity name", Styled(quantity.name, style=STYLES["quantity"]))
        grid.add_row("UUID", Styled(str(quantity.uuid), style=STYLES["uuid"]))
        grid.add_row("Parent entity", Styled(self.imo.entities[quantity.entity].name, style=STYLES["entity"]))
        grid.add_row("Format specification", Styled(str(quantity.format_spec), style=STYLES["uuid"]))

        if quantity.data_files:
            data_file_table = Table()
            data_file_table.add_column("UUID", style=STYLES["uuid"])
            data_file_table.add_column("Upload date")
            data_file_table.add_column("File name", style=STYLES["data_file"])

            for cur_data_file_uuid in quantity.data_files:
                cur_data_file = self.imo.data_files[cur_data_file_uuid]
                data_file_table.add_row(
                    str(cur_data_file.uuid),
                    cur_data_file.upload_date.strftime(DATETIME_FORMAT),
                    cur_data_file.name,
                )

            grid.add_row("Data files", data_file_table)

        self.console.print(grid)

    def show_data_file(self, uuid: UUID) -> None:
        data_file = self.imo.data_files[uuid]

        grid = Table.grid()
        grid.add_column(min_width=25)
        grid.add_column()

        grid.add_row("Data file name", Styled(data_file.name, style=STYLES["data_file"]))
        grid.add_row("UUID", Styled(str(data_file.uuid), style=STYLES["uuid"]))
        grid.add_row("Local path", str(data_file.data_file_local_path))
        grid.add_row("Parent quantity", Styled(str(data_file.quantity), style=STYLES["uuid"]))
        grid.add_row("Comment", data_file.comment)
        grid.add_row("Specification version", data_file.spec_version)

        if data_file.dependencies:
            deps_table = Table()
            deps_table.add_column("UUID", style=STYLES["uuid"])
            deps_table.add_column("Name", style=STYLES["data_file"])

            for cur_dep_uuid in data_file.dependencies:
                cur_dep = self.imo.data_files[cur_dep_uuid]
                deps_table.add_row(str(cur_dep_uuid), cur_dep.name)

            grid.add_row("Dependencies", deps_table)

        releases = []  # type: list[Release]
        for release_tag, release in self.imo.releases.items():
            if data_file.uuid in release.data_files:
                releases.append(release)

        if releases:
            release_table = Table()
            release_table.add_column("Tag")
            release_table.add_column("Date")
            release_table.add_column("Path to this object")

            for cur_release in releases:
                data_file_path = [
                    "/releases",
                    cur_release.tag,
                    self.imo.get_path_for_quantity(data_file.quantity),
                ]
                release_table.add_row(
                    cur_release.tag,
                    cur_release.rel_date.strftime(DATETIME_FORMAT),
                    "/".join(data_file_path),
                )

            grid.add_row("In releases", release_table)

        self.console.print(grid)

    def show_format_spec(self, uuid: UUID) -> None:
        format_spec = self.imo.format_specs[uuid]

        grid = Table.grid()
        grid.add_column(min_width=35)
        grid.add_column()

        grid.add_row("Format specification reference", format_spec.document_ref)
        grid.add_row("UUID", Styled(str(format_spec.uuid), style=STYLES["uuid"]))
        grid.add_row("Title", format_spec.title)
        grid.add_row("Local file", str(format_spec.local_doc_file_path))

        self.console.print(grid)

    def do_pwd(self, _):
        """Print the current position in the tree of entities

        Usage: pwd
        """

        if not self.selected_entity_uuid:
            return False

        self.console.print(
            self.imo.get_path_for_entity(self.selected_entity_uuid),
            style=STYLES["entity"],
        )
        return False

    def do_ls(self, arg):
        """List the entities and quantities at the current level

        Usage: ls [-s] [-e]

        The command accepts the following flags:

            -s     Short format: do not print the UUIDs
            -e     Print entities but no quantities
        """

        params = arg.split()
        short_format = "-s" in params
        only_entities = "-e" in params

        # First print the entities…
        for cur_entity in self.child_entities():
            if not short_format:
                self.console.print(cur_entity.uuid, end="\t", style=STYLES["uuid"])

            self.console.print(f"{cur_entity.name}/", style=STYLES["entity"])

        # …and then the quantities belonging to the current entity
        if not only_entities:
            for cur_quantity in self.child_quantities():
                if not short_format:
                    self.console.print(cur_quantity.uuid, end="\t", style=STYLES["uuid"])

                self.console.print(cur_quantity.name, style=STYLES["quantity"])

        return False

    def list_of_cd_ables_entries(self) -> list[UUID]:
        if not self.selected_entity_uuid:
            # We are still at the root level
            return self.imo.root_entities
        else:
            return [x for x in self.imo.entities if self.imo.query_entity(x).parent == self.selected_entity_uuid]

    def do_cd(self, arg):
        """Enter a child entity

        Usage: cd [NAME | ..]

        Enter an entity within the current position in the entity tree.
        Use '..' to go up one level.
        """

        if arg == "":
            return self.do_pwd(arg)

        if arg == "..":
            if self.selected_entity_uuid:
                self.selected_entity_uuid = self.imo.query_entity(self.selected_entity_uuid).parent
                self.update_prompt()
                return False

        if arg[-1] == "/":
            # Strip the trailing '/'
            arg = arg[:-1]

        # Check that the name is in the alternatives
        for cur_alternative in self.list_of_cd_ables_entries():
            if self.imo.entities[cur_alternative].name == arg:
                self.selected_entity_uuid = cur_alternative
                self.update_prompt()
                return False

        # If we reached this point, it means that we found no match
        self.console.print(f"no entry '{arg}' here", style=STYLES["error"])
        return False

    def complete_cd(self, text: str, _line: str, _beg_idx: int, _end_idx: int) -> list[str]:
        "Called whenever the user presses <TAB> while running the 'cd' command"

        matches = []  # typing: list[str]
        for cur_alternative in self.list_of_cd_ables_entries():
            cur_name = self.imo.entities[cur_alternative].name
            if cur_name.startswith(text):
                matches.append(cur_name)

        return matches

    def do_show(self, obj):
        """Print some information about an entity/quantity/UUID

        Usage: show NAME

        The command is quite liberal in its parameter. It can be one of the following:

        - The UUID of an entity
        - The UUID of a quantity
        - The UUID of a data file
        - The UUID of a format specification
        - The name of a child entity in the current context
        - The name of a child quantity in the current context
        """

        # First try: is `obj` a UUID?
        try:
            uuid = UUID(obj)

            if uuid in self.imo.entities:
                self.show_entity(uuid)
            elif uuid in self.imo.quantities:
                self.show_quantity(uuid)
            elif uuid in self.imo.data_files:
                self.show_data_file(uuid)
            elif uuid in self.imo.format_specs:
                self.show_format_spec(uuid)
            else:
                self.console.print(f'unknown UUID "{uuid}"', style=STYLES["error"])

        except ValueError:
            # No, it's not. Let’s assume it’s an entity
            entity_name = obj
            for cur_entity in self.child_entities():
                if cur_entity.name == entity_name:
                    self.show_entity(cur_entity.uuid)
                    return False

            # If we reach this point, maybe it is a quantity
            quantity_name = obj
            for cur_quantity in self.child_quantities():
                if cur_quantity.name == quantity_name:
                    self.show_quantity(cur_quantity.uuid)
                    return False

            # If we reach this point, it wasn’t a quantity
            self.console.print(f'unknown object "{obj}"', style=STYLES["error"])

        return False

    def complete_show(self, text: str, _line: str, _beg_idx: int, _end_idx: int) -> list[str]:
        "Called whenever the user presses <TAB> while running the 'show' command"

        text_bytes = clean_uuid_from_hyphens(text)
        matches = []  # typing: list[str]
        list_of_possible_matches = list(self.imo.entities) + list(self.imo.quantities) + list(self.imo.data_files)
        for cur_uuid in list_of_possible_matches:
            if cur_uuid.hex.startswith(text_bytes):
                matches.append(str(cur_uuid))

        for cur_entity in self.child_entities():
            if cur_entity.name.startswith(text):
                matches.append(cur_entity.name)

        for cur_quantity in self.child_quantities():
            if cur_quantity.name.startswith(text):
                matches.append(cur_quantity.name)

        return matches

    def do_metadata(self, uuid_str):
        """Print the metadata for a given data file

        Usage: metadata UUID

        where UUID refers to the data file
        """

        try:
            uuid = UUID(uuid_str)
        except ValueError:
            self.console.print("you must provide a valid UUID for a data file", style=STYLES["error"])
            return False

        try:
            data_file = self.imo.data_files[uuid]
        except KeyError:
            self.console.print("the UUID {uuid} does not match any data file".format(uuid=uuid), style=STYLES["error"])
            return False

        self.console.print(data_file.metadata, highlight=True)
        return False

    def matching_uuids(self, text: str, *lists_of_uuid) -> list[str]:
        text_bytes = clean_uuid_from_hyphens(text)
        matches = []  # typing: list[str]
        for cur_list in lists_of_uuid:
            for cur_uuid in list(cur_list):
                if cur_uuid.hex.startswith(text_bytes):
                    matches.append(str(cur_uuid))

        return matches

    def complete_metadata(self, text: str, _line: str, _beg_idx: int, _end_idx: int) -> list[str]:
        "Called whenever the user presses <TAB> while running the 'metadata' command"

        return self.matching_uuids(text, self.imo.data_files)

    def do_open(self, uuid_str: str):
        """Open a data file or a format specification

        Usage: open UUID

        Use the default association provided by your operating system to
        open the data file or format specification associated with UUID.
        """

        try:
            uuid = UUID(uuid_str)
        except ValueError:
            self.console.print(
                "you must provide a valid UUID",
                style=STYLES["error"],
            )
            return False

        if uuid in self.imo.data_files:
            file_name = self.imo.data_files[uuid].data_file_local_path
            if file_name is None:
                self.console.print(
                    'no data file associated with "{}". Try using "metadata" instead of "open"'.format(
                        self.imo.data_files[uuid].name
                    )
                )
                return False

            self.console.print(f'opening data file "{file_name}"')
            open_file(file_name)
        elif uuid in self.imo.format_specs:
            file_name = self.imo.format_specs[uuid].local_doc_file_path
            if file_name is None:
                self.console.print(
                    "no real file for specification document was provided. Contact who created the database"
                )
            self.console.print(f'opening format specification "{file_name}"')
            open_file(file_name)
        else:
            self.console.print(
                f"UUID {uuid} is not a data file or a format specification",
                style=STYLES["error"],
            )

        return False

    def complete_open(self, text: str, _line: str, _beg_idx: int, _end_idx: int) -> list[str]:
        "Called whenever the user presses <TAB> while running the 'open' command"

        return self.matching_uuids(
            text,
            self.imo.data_files.keys(),
            self.imo.format_specs.keys(),
        )

    def do_releases(self, _):
        """Print a list of the releases defined in the database

        Usage: releases
        """

        table = Table()
        table.add_column("Name")
        table.add_column("Date")
        table.add_column("Comments")

        for cur_release_name, cur_release in self.imo.releases.items():
            table.add_row(
                cur_release_name,
                cur_release.rel_date.strftime(DATETIME_FORMAT),
                cur_release.comment,
            )

        self.console.print(table)

    def _populate_subtree(self, tree, entity_uuid: UUID | None) -> None:
        for cur_entity in self.child_entities(entity_uuid):
            cur_tree_node = tree.add(cur_entity.name, style=STYLES["entity"])
            self._populate_subtree(cur_tree_node, cur_entity.uuid)

        for cur_quantity in self.child_quantities(entity_uuid):
            tree.add(cur_quantity.name, style=STYLES["quantity"])

    def do_tree(self, _):
        """Print a tree of all the elements within the current entity

        Usage: tree
        """

        if self.selected_entity_uuid:
            selected_entity_name = self.imo.entities[self.selected_entity_uuid].name
        else:
            selected_entity_name = "/"

        tree = Tree(f"Children of {selected_entity_name}")
        self._populate_subtree(tree, self.selected_entity_uuid)

        self.console.print(tree)

    def do_quit(self, _):
        """Quit the program

        Usage: quit
        """
        return True

    def do_EOF(self, _):
        "Quit the program"
        return True

    def default(self, line):
        self.console.print(line, style=STYLES["error"])


def parse_args():
    parser = ArgumentParser(
        prog="Libinsdb browser",
        description="Navigate in a InstrumentDB database",
    )
    parser.add_argument(
        "--no-colors",
        help="Disable colors in the program",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-c",
        "--command",
        type=str,
        default=None,
        help="Run a command and quit",
    )
    parser.add_argument(
        "input_file",
        help='Path to the schema file to open (e.g., "/storage/schema.json")',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    browser = ImoBrowser(
        input_file_path=args.input_file,
        force_terminal=not args.no_colors,
    )

    if args.command:
        browser.onecmd(args.command)
    else:
        browser.cmdloop()


if __name__ == "__main__":
    main()
