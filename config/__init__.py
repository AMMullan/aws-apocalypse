CONFIG = {
    'ALLOW_EXCEPTIONS': False,
    'EXCEPTION_TAGS': ['exempt:nuke'],
}

# Script will NOT operate in these accounts
BLACKLIST_ACCOUNTS = []

# Script will ONLY operate in these accounts
WHITELIST_ACCOUNTS = []

# Resources that work in the "global" region
GLOBAL_RESOURCES = [
    'CloudWatch::Dashboard',
    'IAM::User',
    'IAM::Role',
    'IAM::Group',
    'IAM::Policy',
    'IAM::InstanceProfile',
]
