from __future__ import annotations
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import object_session

from lation.modules.base.models.end_user import EndUser, EndUserToken


class LoginEndUserToken(EndUserToken):
    __lation__ = {
        'polymorphic_identity': 'login_end_user_token'
    }


def login(self) -> LoginEndUserToken:
    session = object_session(self)
    now = datetime.utcnow()
    token = LoginEndUserToken(end_user=self,
                                value=uuid.uuid4().hex,
                                expiration_time=now + timedelta(days=10))
    session.add(token)
    self.last_login_time = now
    return token

EndUser.login = login
