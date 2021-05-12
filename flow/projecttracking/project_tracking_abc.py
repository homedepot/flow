from abc import ABCMeta, abstractmethod


class Project_Tracking(metaclass=ABCMeta):
    @abstractmethod
    def get_details_for_all_stories(self, story_list):
        pass

    @abstractmethod
    def determine_semantic_version_bump(self, story_details):
        pass

    @abstractmethod
    def extract_story_id_from_commit_messages(self, commit_messages):
        pass

    @abstractmethod
    def tag_stories_in_commit(self, story_list):
        pass

    @abstractmethod
    def flatten_story_details(self, story_details):
        pass