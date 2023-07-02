from watchdog.events import FileSystemEventHandler
from my_codebase import MyCodebase
import time
from watchdog.observers import Observer


class UpdateHandler(FileSystemEventHandler):
    """
    A class used to handle file system events, specifically modifications and creations of .py files.

    This class is a subclass of the watchdog.events.FileSystemEventHandler class and overrides its
    on_modified and on_created methods to interact with a LocalRepositoryDB instance.

    ...

    Attributes
    ----------
    db : LocalRepositoryDB
        an instance of the LocalRepositoryDB class that this handler will use to update
        the database when a .py file event occurs

    Methods
    -------
    on_modified(event):
        This method is triggered when a file is modified in the observed directory. If the modified
        file ends with '.py', it updates the database via the LocalRepositoryDB instance.

    on_created(event):
        This method is triggered when a file is created in the observed directory. If the created
        file ends with '.py', it updates the database via the LocalRepositoryDB instance.
    """

    def __init__(self, db: MyCodebase):
        self.db = db

    def on_modified(self, event):
        print(f"event type: {event.event_type}  path : {event.src_path}")
        if event.src_path.endswith(".py"):
            print("Python file changed, refreshing DB.")
            # Instantiate your class here to refresh DB
            self.db.update_file(event.src_path)

    def on_created(self, event):
        print(f"event type: {event.event_type}  path : {event.src_path}")
        if event.src_path.endswith(".py"):
            print("Python file created, refreshing DB.")
            # Instantiate your class here to refresh DB
            self.db.update_file(event.src_path)


if __name__ == "__main__":
    # Create a LocalRepositoryDB object
    db = MyCodebase()

    # Create an event handler
    event_handler = UpdateHandler(db)

    # Create an observer
    observer = Observer()

    # Set the observer to follow the directory of interest
    path = "/path/to/your/directory"
    observer.schedule(event_handler, path, recursive=True)

    # Start the observer
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
