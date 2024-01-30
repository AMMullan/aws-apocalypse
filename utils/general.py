from config import config


def check_delete(tags: dict):
    if not config.ALLOW_EXCEPTIONS:
        return True

    return not any(
        tag in tags and tags[tag].lower() == 'true' for tag in config.EXCEPTION_TAGS
    )
