from dataclasses import dataclass, field


@dataclass
class Config:
    ALLOW_EXCEPTIONS: bool = False
    EXCEPTION_TAGS: set[str] = field(default_factory=lambda: {'exempt:nuke'})

    COMMAND: str = 'inspect-aws'
    OUTPUT_FORMAT: str = 'rich'

    # Script will NOT operate in these accounts
    BLACKLIST_ACCOUNTS: set[str] = field(default_factory=set)

    # Script will ONLY operate in these accounts
    WHITELIST_ACCOUNTS: set[str] = field(default_factory=set)

    # Resources that work in the "global" region
    GLOBAL_RESOURCES: list[str] = field(
        default_factory=lambda: [
            'CloudWatch::Dashboard',
            'IAM::User',
            'IAM::Role',
            'IAM::Group',
            'IAM::Policy',
            'IAM::InstanceProfile',
        ]
    )

    REGIONS: set[str] = field(default_factory=set)

    INCLUDE_RESOURCES: set[str] = field(default_factory=set)
    INCLUDE_SERVICES: set[str] = field(default_factory=set)
    EXCLUDE_RESOURCES: set[str] = field(default_factory=set)
    EXCLUDE_SERVICES: set[str] = field(default_factory=set)

    def add_region(self, region_name: str) -> None:
        self.REGIONS.add(region_name)

    def remove_region(self, region_name: str) -> None:
        self.REGIONS.discard(region_name)

    def add_blacklisted_account(self, account_id: str) -> None:
        self.BLACKLIST_ACCOUNTS.add(account_id)

    def add_whitelisted_account(self, account_id: str) -> None:
        self.WHITELIST_ACCOUNTS.add(account_id)

    def add_custom_exception_tag(self, tag: str) -> None:
        self.EXCEPTION_TAGS.add(tag)

    def add_included_resource(self, resource: str) -> None:
        self.INCLUDE_RESOURCES.add(resource)

    def add_included_service(self, service: str) -> None:
        self.INCLUDE_SERVICES.add(service)

    def add_excluded_resource(self, resource: str) -> None:
        self.EXCLUDE_RESOURCES.add(resource)

    def add_excluded_service(self, service: str) -> None:
        self.EXCLUDE_SERVICES.add(service)


config = Config()
