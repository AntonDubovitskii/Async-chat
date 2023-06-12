import datetime
import os

from sqlalchemy import create_engine, String, DateTime, TEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class ClientDatabase:
    """
    Класс - оболочка для работы с базой данных клиента.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy 2.0 ORM и используется декларативный подход.
    """
    class Base(DeclarativeBase):
        """Базовый декларативный класс для дальнейшего наследования."""
        pass

    class KnownUsers(Base):
        """
        Класс, реализующий создание таблицы всех пользователей в базе данных,
        а также взаимодействие с ней.
        """
        __tablename__ = 'known_users'
        id: Mapped[int] = mapped_column(primary_key=True)
        username: Mapped[str] = mapped_column(String(50))

        def __init__(self, username):
            super().__init__()
            self.id = None
            self.username = username

        def __repr__(self):
            return f'Username: {self.username}'

    class MessageHistory(Base):
        """
        Класс, реализующий создание таблицы статистики переданных сообщений,
        а также взаимодействие с ней.
        """
        __tablename__ = 'message_history'
        id: Mapped[int] = mapped_column(primary_key=True)
        from_user: Mapped[str] = mapped_column(String(50))
        to_user: Mapped[str] = mapped_column(String(50))
        message: Mapped[str] = mapped_column(TEXT)
        date: Mapped[datetime.datetime] = mapped_column(
            DateTime(timezone=True), default=datetime.datetime.now())

        def __init__(self, from_user, to_user, message):
            super().__init__()
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message

        def __repr__(self):
            return f'Message: {self.message}\nFrom: {self.from_user}\nTo: {self.to_user}'

    class Contacts(Base):
        """
        Класс, реализующий создание таблицы контактов, а также взаимодействие с ней.
        """
        __tablename__ = 'contacts'
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(50), unique=True)

        def __init__(self, name):
            super().__init__()
            self.id = None
            self.name = name

        def __repr__(self):
            return f'Contact name: {self.name}'

    def __init__(self, name):
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.engine = create_engine(f'sqlite:///{os.path.join(path, filename)}',
                                    echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """
        Метод, добавляющий контакт в базу данных
        :param contact:
        :return:
        """
        if not self.session.query(
                self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def contacts_clear(self):
        """
        Метод, очищающий таблицу со списком контактов.
        :return:
        """
        self.session.query(self.Contacts).delete()

    def del_contact(self, contact):
        """
        Метод, удаляющий указанный контакт.
        :param contact:
        :return:
        """
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def add_users(self, users_list):
        """
        Метод, заполняющий таблицу известных пользователей.
        :param users_list:
        :return:
        """
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        """
        Метод, сохраняющий сообщение в базе данных.
        :param from_user:
        :param to_user:
        :param message:
        :return:
        """
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        """
        Метод, возвращающий список всех контактов.
        :return:
        """
        return [contact[0]
                for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        """
        Метод, возвращающий список всех известных пользователей.
        :return:
        """
        return [user[0]
                for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        """
        Метод, выполняющий проверку присутствия пользователя в базе данных.
        :param user:
        :return:
        """
        if self.session.query(self.KnownUsers).filter_by(
                username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        """
        Метод, выполняющий проверку присутствия контакта в базе данных.
        :param contact:
        :return:
        """
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, from_who=None, to_who=None):
        """
        Метод, возвращающий историю сообщения определенного пользователя.
        :param from_who:
        :param to_who:
        :return:
        """
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]


if __name__ == '__main__':
    test_db = ClientDatabase('test1')
    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)
    test_db.add_contact('test4')
    test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    test_db.save_message(
        'test1',
        'test2',
        f'Привет! я тестовое сообщение от {datetime.datetime.now()}!')
    test_db.save_message(
        'test2',
        'test1',
        f'Привет! я другое тестовое сообщение от {datetime.datetime.now()}!')
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user('test1'))
    print(test_db.check_user('test10'))
    print(test_db.get_history('test2'))
    print(test_db.get_history(to_who='test2'))
    print(test_db.get_history('test3'))
    test_db.del_contact('test4')
    print(test_db.get_contacts())
