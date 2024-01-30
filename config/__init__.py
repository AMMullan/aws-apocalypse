from dataclasses import dataclass, field


@dataclass
class Config:
    ALLOW_EXCEPTIONS: bool = False
    EXCEPTION_TAGS: set[str] = field(default_factory=lambda: {'exempt:nuke'})

    # Script will NOT operate in these accounts
    BLACKLIST_ACCOUNTS: list[str] = field(default_factory=list)

    # Script will ONLY operate in these accounts
    WHITELIST_ACCOUNTS: list[str] = field(default_factory=list)

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
    EXCLUDE_REGIONS: set[str] = field(default_factory=set)

    INCLUDE_RESOURCES: list[str] = field(default_factory=list)
    INCLUDE_SERVICES: list[str] = field(default_factory=list)
    EXCLUDE_RESOURCES: list[str] = field(default_factory=list)
    EXCLUDE_SERVICES: list[str] = field(default_factory=list)

    def add_blacklisted_account(self, account_id: str) -> None:
        self.BLACKLIST_ACCOUNTS.append(account_id)

    def add_whitelisted_account(self, account_id: str) -> None:
        self.WHITELIST_ACCOUNTS.append(account_id)

    def add_custom_exception_tag(self, tag: str) -> None:
        self.EXCEPTION_TAGS.add(tag)

    def add_included_resource(self, resource: str) -> None:
        self.INCLUDE_RESOURCES.append(resource)

    def add_included_service(self, service: str) -> None:
        self.INCLUDE_SERVICES.append(service)

    def add_excluded_resource(self, resource: str) -> None:
        self.EXCLUDE_RESOURCES.append(resource)

    def add_excluded_service(self, service: str) -> None:
        self.EXCLUDE_SERVICES.append(service)


config = Config()
