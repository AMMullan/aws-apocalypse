import json
from abc import ABC, abstractmethod
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text

from config import config
from registry import query_registry


class OutputHandler(ABC):
    def __init__(self, session, console: Optional[Console] = None) -> None:
        self.session = session
        if console:
            if isinstance(console, Console):
                self.console = console
            else:
                raise ValueError('Invalid Type: Console Expected')

    @abstractmethod
    def retrieve_data(self, resource_types: list[str], regions: list[str]) -> None:
        pass


class JSONOutputHandler(OutputHandler):
    def retrieve_data(
        self, resource_types: list[str], regions: list[str] | set[str]
    ) -> dict[str, dict[str, dict]]:
        resource_output = {}

        for resource_type in resource_types:
            delete_function = query_registry[resource_type]
            for region in regions:
                if (
                    region == 'global' and resource_type not in config.GLOBAL_RESOURCES
                ) or (region != 'global' and resource_type in config.GLOBAL_RESOURCES):
                    continue

                if results := delete_function(self.session, region):
                    resource_output.setdefault(region, {}).update(
                        {resource_type: results}
                    )

        print(json.dumps(resource_output))
        return resource_output


class RichOutputHandler(OutputHandler):
    def display_rich_resource_table(self, resources: dict) -> None:
        table = Table()
        table.add_column('Region')
        table.add_column('Resource Type')
        table.add_column('Identifier')

        for region, regional_resources in resources.items():
            for resource_type, resource_arns in regional_resources.items():
                for arn in resource_arns:
                    table.add_row(region, resource_type, arn)

        self.console.print(table)

    def retrieve_data(
        self, resource_types: list[str], regions: list[str] | set[str]
    ) -> dict[str, dict[str, dict]]:
        resource_output = {}

        for resource_type in resource_types:
            delete_function = query_registry[resource_type]
            for region in regions:
                if (
                    region == 'global' and resource_type not in config.GLOBAL_RESOURCES
                ) or (region != 'global' and resource_type in config.GLOBAL_RESOURCES):
                    continue

                with self.console.status(
                    f'[bold green]Searching {region} For {resource_type}',
                    spinner='aesthetic',
                ):
                    if results := delete_function(self.session, region):
                        resource_output.setdefault(region, {}).update(
                            {resource_type: results}
                        )

                    self.console.print(
                        Text.assemble(
                            (" INFO ", 'bold grey35 on green'),
                            ' ',
                            (
                                f'{resource_type} | Found {len(results or [])} resources in {region}',
                                'green',
                            ),
                        )
                    )

        if resource_output:
            self.console.print('\n# [yellow] Found AWS Resources\n')
            self.display_rich_resource_table(resource_output)
            return resource_output

        self.console.print('\n# [green] No Resources Found')
        return {}
