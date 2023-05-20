class UserDoesNotExist(Exception):
    def __str__(self):
        return 'Попытка написать несуществующему пользователю!'

