
class Scheduler:
    # TODO: Have one class 'Scheduler'. Its contructor receives an event queue to fire
    #       events into.
    #       There is a method 'submit' that takes an event and a (relative) time stamp.
    #       This method creates a task that waits until the time stamp has expired and then
    #       enqueues the event into the event queue. The task must be created with asyncio's
    #       'create_task' and then kept around in the Scheduler, such that it is not deallocated.
    #       The last step in each task is to remove itself from the list of tasks.
    #       There should also be a method 'clear' that unschedules all pending tasks.
    #       There should be a method async def next, that yields the next event once one is ready.
    pass