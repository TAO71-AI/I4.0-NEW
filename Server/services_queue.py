import time

class Queue():
    def __init__(self, ModelName: str, MaxSimultaneousUsers: int) -> None:
        self.MODEL_NAME = ModelName
        self.MAX_SIMULTANEOUS_USERS = MaxSimultaneousUsers
        self.__waiting_uids__ = []
        self.__processing_uids__ = []
        self.TokensPerSecond = None
        self.FirstTokenSeconds = None
    
    def CreateNewWaitingID(self, Prioritize: bool = False) -> int:
        if (Prioritize):
            negativeUIDs = [uid for uid in self.__waiting_uids__ + self.__processing_uids__ if (uid <= 0)]
            newUID = -len(negativeUIDs)
        else:
            positiveUIDs = [uid for uid in self.__waiting_uids__ + self.__processing_uids__ if (uid > 0)]
            newUID = len(positiveUIDs) + 1
        
        self.__waiting_uids__.append(newUID)
        return newUID
    
    def DeleteUID(self, UID: int) -> None:
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

Queues: list[Queue] = []

def GetQueueForModel(ModelName: str) -> Queue | None:
    for queue in Queues:
        if (queue.MODEL_NAME == ModelName):
            return queue
    
    return None