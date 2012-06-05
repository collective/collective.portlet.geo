from ZPublisher.BaseRequest import RequestContainer
from ZPublisher import Publish

from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import UnrestrictedUser

def loginAsUnrestrictedUser():
    """Log in as unrestricted user. Returns old user.

    Example usage:

      >>> old_user = loginAsUnrestrictedUser()
      >>> ...
      >>> loginAsUser(old_user)

    """

    current_user = getSecurityManager().getUser()
    newSecurityManager(None, UnrestrictedUser('manager', '', ['Manager'], []))
    return current_user

def loginAsUser(user):
    newSecurityManager(None, user)
