import datetime
import os
from typing import List

from sqlalchemy import create_engine, String, INT, DateTime, ForeignKey, Integer, TEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.sql import func


class ServerStorage:
    class Base(DeclarativeBase):
        pass

    class Users(Base):
        __tablename__ = 'user_account'
        id: Mapped[int] = mapped_column(primary_key=True)
        login: Mapped[str] = mapped_column(String(50))
        last_login: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now())
        pubkey: Mapped[str] = mapped_column(TEXT, nullable=True)
        passwd_hash: Mapped[str] = mapped_column(String)

        session: Mapped[List["LoginSessions"]] = relationship(back_populates='account')
        active: Mapped["ActiveUsers"] = relationship(back_populates='account')
        history: Mapped[List["UsersHistory"]] = relationship(back_populates='account')

        def __init__(self, login, passwd_hash):
            super().__init__()
            self.login = login
            self.id = None
            self.pubkey = None
            self.passwd_hash = passwd_hash

        def __repr__(self):
            return f'Login: {self.login}, Date: {self.last_login}'

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

    class UsersContacts(Base):
        __tablename__ = 'contacts'
        id: Mapped[int] = mapped_column(primary_key=True)

        user_id = mapped_column(Integer, ForeignKey('user_account.id'))
        contact_id = mapped_column(Integer, ForeignKey('user_account.id'))

        user = relationship("Users", foreign_keys="[UsersContacts.user_id]")
        contact = relationship("Users", foreign_keys="[UsersContacts.contact_id]")

        def __init__(self, user_id, contact_id):
            super().__init__()
            self.id = None
            self.user_id = user_id
            self.contact_id = contact_id

    class UsersHistory(Base):
        __tablename__ = 'users_history'
        id: Mapped[int] = mapped_column(primary_key=True)
        user: Mapped[int] = mapped_column(ForeignKey('user_account.id'))
        sent: Mapped[int] = mapped_column(INT)
        accepted: Mapped[int] = mapped_column(INT)
        account: Mapped["Users"] = relationship(back_populates='history')

        def __init__(self, user):
            super().__init__()
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

        def __repr__(self):
            return f'User: {self.user}, send: {self.sent}, accepted: {self.accepted}'

    def __init__(self, path):
        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, login, ip_address, port, key):

        rez = self.session.query(self.Users).filter_by(login=login)

        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        new_active_user = self.ActiveUsers(
            user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginSessions(
            user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def add_user(self, name, passwd_hash):
        '''
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        '''
        user_row = self.Users(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        user = self.session.query(self.Users).filter_by(login=name).first()
        self.session.query(self.ActiveUsers).filter_by(account_id=user.id).delete()
        self.session.query(self.LoginSessions).filter_by(name=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user_id=user.id).delete()
        self.session.query(
            self.UsersContacts).filter_by(
            contact_id=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.Users).filter_by(login=name).delete()
        self.session.commit()

    def get_hash(self, name):
        '''Метод получения хэша пароля пользователя.'''
        user = self.session.query(self.Users).filter_by(login=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        user = self.session.query(self.Users).filter_by(login=name).first()
        return user.pubkey

    def check_user(self, name):
        if self.session.query(self.Users).filter_by(login=name).count():
            return True
        else:
            return False

    def user_logout(self, username):
        user = self.session.query(self.Users).filter_by(login=username).first()
        print(user.login)
        self.session.query(self.ActiveUsers).filter_by(account_id=user.id).delete()

        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.Users.login,
            self.Users.last_login
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

    def process_message(self, sender, recipient):

        sender = self.session.query(self.Users).filter_by(login=sender).first().id
        recipient = self.session.query(self.Users).filter_by(login=recipient).first().id

        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def message_history(self):
        query = self.session.query(
            self.Users.login,
            self.Users.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.Users)
        return query.all()

    def add_contact(self, username, contact_name):

        user = self.session.query(self.Users).filter_by(login=username).first()
        contact = self.session.query(self.Users).filter_by(login=contact_name).first()

        if not contact or self.session.query(self.UsersContacts).filter_by(user_id=user.id, contact_id=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, username, contact_name):

        user = self.session.query(self.Users).filter_by(login=username).first()
        contact = self.session.query(self.Users).filter_by(login=contact_name).first()

        if not contact:
            return

        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user_id == user.id,
            self.UsersContacts.contact_id == contact.id
        ).delete()
        self.session.commit()

    def get_contacts(self, username):

        user = self.session.query(self.Users).filter_by(login=username).one()

        query = self.session.query(self.UsersContacts, self.Users.login).filter_by(user_id=user.id).join(self.Users, self.UsersContacts.contact_id == self.Users.id)

        return [contact[1] for contact in query.all()]


if __name__ == '__main__':
    test_db = ServerStorage()

    test_db.user_login('Tom', '192.168.1.113', 8080)
    test_db.user_login('Tim', '192.168.1.113', 8081)
    # print(test_db.users_list())
    print(test_db.active_users_list())
    test_db.user_logout('Tom')
    print(test_db.login_history('Tom'))
    test_db.add_contact('Tom', 'Tim')
    test_db.add_contact('Tim', 'Tom')
    test_db.add_contact('test1', 'test2')
    test_db.remove_contact('test1', 'test2')
    test_db.process_message('Tom', 'Tim')
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(test_db.get_contacts('Tom'))
    # print(test_db.message_history())

