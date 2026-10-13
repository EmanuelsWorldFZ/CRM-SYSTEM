from crm.models import Client, User, UserRole


def is_admin(user: User) -> bool:
    return user.is_authenticated and user.role == UserRole.ADMIN


def can_manage_client(user: User, client: Client) -> bool:
    return is_admin(user) or client.owner_id == user.id
