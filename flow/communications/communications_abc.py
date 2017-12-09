from abc import ABCMeta, abstractmethod


class communications(metaclass=ABCMeta):
    @abstractmethod
    def publish_deployment(self, story_details):
        pass

    @abstractmethod
    def publish_error(sender, message, class_name, method_name):
        pass