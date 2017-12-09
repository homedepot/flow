class Logger:

    instance = None

    class __Logger:
        log_file = None

        def __init__(self, message):
            self.log_file = open(".flow.log.txt", "a")
            self.log_file.write('\r\n' + message)

    def __init__(self, message):
        if not Logger.instance:
            Logger.instance = Logger.__Logger(message)
        else:
            Logger.instance.log_file.write('\r\n' + message)

    def __getattr__(self, name):
        return getattr(self.instance, name)
