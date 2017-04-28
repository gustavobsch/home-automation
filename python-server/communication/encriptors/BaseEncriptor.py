import abc

class BaseEncriptor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def encrypt(self, text):
        pass

    @abc.abstractmethod
    def decrypt(self, text):
        pass

    @abc.abstractmethod
    def get_name(self):
        pass