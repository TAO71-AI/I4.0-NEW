import time

class Queue():
    def __init__(self, ModelName: str, MaxSimultaneousUsers: int) -> None:
        self.MODEL_NAME = ModelName
        self.MAX_SIMULTANEOUS_USERS = MaxSimultaneousUsers
        self.__waiting_uids__ = []
        self.__processing_uids__ = []
        self.__next_uid__ = 0
        self.TokensPerSecond = None
        self.FirstTokenSeconds = None
    
    def CreateNewWaitingID(self, Prioritize: bool = False) -> int:
        if (
            1 not in self.__waiting_uids__ and 1 not in self.__processing_uids__ and
            -1 not in self.__waiting_uids__ and -1 not in self.__processing_uids__
        ):
            self.__next_uid__ = 0

        self.__next_uid__ += 1

        if (Prioritize):
            newUID = -self.__next_uid__
        else:
            newUID = self.__next_uid__
        
        self.__waiting_uids__.append(newUID)
        return newUID
    
    def DeleteUID(self, UID: int | list[int]) -> None:
        if (isinstance(UID, list)):
            for uid in UID:
                self.DeleteUID(uid)

        if (UID in self.__waiting_uids__):
            self.__waiting_uids__.remove(UID)
        
        if (UID in self.__processing_uids__):
            self.__processing_uids__.remove(UID)

    def ProcessNextUser(self) -> None:
        priorityUsers = [uid for uid in self.__waiting_uids__ if (uid <= 0)]
        nonPriorityUsers = [uid for uid in self.__waiting_uids__ if (uid > 0)]

        if (len(priorityUsers) > 0):
            selectedUID = max(priorityUsers)
        elif (len(nonPriorityUsers) > 0):
            selectedUID = min(nonPriorityUsers)
        else:
            selectedUID = None
        
        if (selectedUID is None):
            return
        
        self.__waiting_uids__.remove(selectedUID)
        self.__processing_uids__.append(selectedUID)
    
    def WaitForProcessing(self, UID: int) -> None:
        while (UID in self.__waiting_uids__ and UID not in self.__processing_uids__):
            if (len(self.__processing_uids__) < self.MAX_SIMULTANEOUS_USERS):
                self.ProcessNextUser()

            time.sleep(0.1)
    
    def GetUsersBeforeUID(self, UID: int) -> int:
        if (UID in self.__processing_uids__):
            return 0
        
        if (UID not in self.__waiting_uids__):
            return -1
        
        priorityUsers = [uid for uid in self.__waiting_uids__ if (uid <= 0)]
        nonPriorityUsers = [uid for uid in self.__waiting_uids__ if (uid > 0)]

        usersBefore = 0

        if (UID <= 0):
            for uid in priorityUsers:
                if (uid > UID):
                    usersBefore += 1
        else:
            usersBefore += len(priorityUsers)

            for uid in nonPriorityUsers:
                if (uid < UID):
                    usersBefore += 1
        
        return usersBefore

Queues: list[Queue] = []

def GetQueueForModel(ModelName: str) -> Queue | None:
    for queue in Queues:
        if (queue.MODEL_NAME == ModelName):
            return queue
    
    return None