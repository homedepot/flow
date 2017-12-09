from abc import ABCMeta, abstractmethod


class Project_Tracking(metaclass=ABCMeta):
    @abstractmethod
    def get_details_for_all_stories(self, story_list):
        pass

    @abstractmethod
    def determine_semantic_version_bump(self, story_details):
        pass
