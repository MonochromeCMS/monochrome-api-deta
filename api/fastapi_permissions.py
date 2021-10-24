""" Row Level Permissions for FastAPI
This module provides an implementation for row level permissions for the
FastAPI framework. This is heavily inspired / ripped off the Pyramids Web
Framework, so all cudos to them!
"""

__version__ = "0.2.7"

from functools import partial
from itertools import chain
from inspect import iscoroutinefunction
from typing import Any

from fastapi import Depends, HTTPException, status

# constants

Allow = "Allow"  # acl "allow" action
Deny = "Deny"  # acl "deny" action

Everyone = "system:everyone"  # user principal for everyone
Authenticated = "system:authenticated"  # authenticated user principal


class _AllPermissions:
    """special container class for the all permissions constant
    first try was to override the __contains__ method of a str instance,
    but it turns out to be readonly...
    """

    def __contains__(self, other):
        """returns alway true any permission"""
        return True

    def __str__(self):
        """string representation"""
        return "permissions:*"


All = _AllPermissions()


DENY_ALL = (Deny, Everyone, All)  # acl shorthand, denies anything
ALOW_ALL = (Allow, Everyone, All)  # acl shorthand, allows everything


# the exception that will be raised, if no sufficient permissions are found
# can be configured in the configure_permissions() function
permission_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Insufficient permissions",
    headers={"WWW-Authenticate": "Bearer"},
)

authentificated_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authentificated",
    headers={"WWW-Authenticate": "Bearer"},
)


def configure_permissions(
    active_principals_func: Any,
        perm_exception: HTTPException = permission_exception,
        auth_exception: HTTPException = authentificated_exception,
):
    """sets the basic configuration for the permissions' system
    active_principals_func:
        a dependency that returns the principals of the current active user
    permission_exception:
        the exception used if a permission is denied
    returns: permission_dependency_factory function,
             with some parameters already provisioned
    """
    active_principals_func = Depends(active_principals_func)

    return partial(
        permission_dependency_factory,
        active_principals_func=active_principals_func,
        perm_exception=perm_exception,
        auth_exception=auth_exception,
    )


def permission_dependency_factory(
    permission: str,
    resource: Any,
    active_principals_func: Any,
    auth_exception: HTTPException,
    perm_exception: HTTPException,
):
    """returns a function that acts as a dependable for checking permissions
    This is the actual function used for creating the permission dependency,
    with the help of fucntools.partial in the "configure_permissions()"
    function.
    permission:
        the permission to check
    resource:
        the resource that will be accessed
    active_principals_func (provisioned  by configure_permissions):
        a dependency that returns the principals of the current active user
    permission_exception (provisioned  by configure_permissions):
        exception if permission is denied
    returns: dependency function for "Depends()"
    """
    if callable(resource):
        dependable_resource = Depends(resource)
    else:
        dependable_resource = Depends(lambda: resource)

    # to get the caller signature right, we need to add only the resource and
    # user dependable in the definition
    # the permission itself is available through the outer function scope
    async def permission_dependency(resource=dependable_resource, principals=active_principals_func):
        if await has_permission(principals, permission, resource):
            return resource
        if Authenticated not in principals:
            raise auth_exception
        raise perm_exception

    return Depends(permission_dependency)


async def has_permission(user_principals: list, requested_permission: str, resource: Any):
    """checks if a user has the permission for a resource
    The order of the function parameters can be remembered like "Joe eat apple"
    user_principals: the principals of a user
    requested_permission: the permission that should be checked
    resource: the object the user wants to access, must provide an ACL
    returns bool: permission granted or denied
    """
    acl = await normalize_acl(resource)

    for action, principals, permissions in acl:
        if isinstance(permissions, str):
            permissions = {permissions}
        if requested_permission in permissions:
            if all(principal in user_principals for principal in principals):
                return action == Allow
    return False


async def list_permissions(user_principals: list, resource: Any):
    """lists all permissions of a user for a resouce
    user_principals: the principals of a user
    resource: the object the user wants to access, must provide an ACL
    returns dict: every available permission of the resource as key
                  and True / False as value if the permission is granted.
    """
    acl = await normalize_acl(resource)

    acl_permissions = (permissions for _, _, permissions in acl)
    as_iterables = ({p} if not is_like_list(p) else p for p in acl_permissions)
    permissions = set(chain.from_iterable(as_iterables))

    return {str(p): await has_permission(user_principals, p, acl) for p in permissions}


# utility functions


async def normalize_acl(resource: Any):
    """returns the access controll list for a resource
    If the resource is not an acl list itself it needs to have an "__acl__"
    attribute. If the "__acl__" attribute is a callable, it will be called and
    the result of the call returned.
    An existing __acl__ attribute takes precedence before checking if it is an
    iterable.
    """
    acl = getattr(resource, "__acl__", None)
    if iscoroutinefunction(acl):
        return await acl()
    elif callable(acl):
        return acl()
    elif acl is not None:
        return acl
    elif is_like_list(resource):
        return resource
    return []


def is_like_list(something):
    """checks if something is iterable but not a string"""
    if isinstance(something, str):
        return False
    return hasattr(something, "__iter__")
