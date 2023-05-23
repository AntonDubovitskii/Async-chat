import datetime
from typing import Optional, List

from sqlalchemy import create_engine, String, INT, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.sql import func
from sqlalchemy_utils import database_exists, create_database


class ServerStorage:

    class Base(DeclarativeBase):
        pass

    class Users(Base):
        __tablename__ = 'user_account'
        id: Mapped[int] = mapped_column(primary_key=True)
        login: Mapped[str] = mapped_column(String(50))
        info: Mapped[Optional[str]]
        session: Mapped[List["LoginSessions"]] = relationship(back_populates='account')
        active: Mapped["ActiveUsers"] = relationship(back_populates='account')

        def __init__(self, login, info):
            super().__init__()
            self.login = login
            self.info = info
            self.id = None

        def __repr__(self):
            return f'Login: {self.login}, Info: {self.info}'

    class ActiveUsers(Base):
        __tablename__ = 'active_user'
        id: Mapped[int] = mapped_column(primary_key=True)
        ip_address: Mapped[str] = mapped_column(String(20))
        port: Mapped[str] = mapped_column(INT)
        login_time: Mapped[datetime.datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now())
        account_id: Mapped[int] = mapped_column(ForeignKey('user_account.id'))
        account: Mapped["Users"] = relationship(back_populates='active')

        def __init__(self, account_id, ip_address, port, login_time):
            super().__init__()
            self.account_id = account_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginSessions(Base):
        __tablename__ = 'user_session'
        id: Mapped[int] = mapped_column(primary_key=True)
        ip_address: Mapped[str] = mapped_column(String(20))
        port: Mapped[str] = mapped_column(INT)
        login_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
        name: Mapped[int] = mapped_column(ForeignKey('user_account.id'))
        account: Mapped["Users"] = relationship(back_populates='session')

        def __init__(self, name, loging_time, ip_address, port):
            super().__init__()
            self.id = None
            self.name = name
            self.loging_time = loging_time
            self.ip_address = ip_address
            self.port = port

        def __repr__(self):
            return f'Saved session, ip_address: {self.ip_address}, port: {self.port}, time: {self.login_time}'

    def __init__(self):
        self.engine = create_engine('sqlite:///db.sqlite', echo=True, pool_recycle=7200)
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

        self.Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, login, ip_address, port, info=''):

        rez = self.session.query(self.Users).filter_by(login=login)

        if rez.count():
            user = rez.first()
        else:
            user = self.Users(login, info)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginSessions(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.Users).filter_by(login=username).first()

        self.session.query(self.ActiveUsers).filter_by(account_id=user.id).delete()

        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.Users.login,
        )
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.Users.login,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.Users)
        return query.all()

    def login_history(self, username=None):

        query = self.session.query(self.Users.login,
                                   self.LoginSessions.login_time,
                                   self.LoginSessions.ip_address,
                                   self.LoginSessions.port
                                   ).join(self.Users)

        if username:
            query = query.filter(self.Users.login == username)
        return query.all()


if __name__ == '__main__':

    test_db = ServerStorage()

    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)

    print(test_db.active_users_list())

    test_db.user_logout('client_1')

    print(test_db.active_users_list())

    test_db.login_history('client_1')

    print(test_db.users_list())

