# -*- coding: utf-8 -*-
import logging as _logging
import sys

__author__ = 'luckydonald'
__all__ = ["logging", "ColoredFormatter", "ColoredStreamHandler", "LevelByNameFilter"]


class ColoredFormatter(_logging.Formatter):
    class Color(object):
        """
         utility to return ansi colored text.
         just to store the colors next to the function.
        """
        # Color codes: http://misc.flogisoft.com/bash/tip_colors_and_formatting

        def __init__(self, formatter):
            self.formatter = formatter

        # end def

        colors = {
            'default': 39,
            'black': 30,
            'red': 31,
            'green': 32,
            'yellow': 33,
            'blue': 34,
            'magenta': 35,
            'cyan': 36,
            'white': 37,
            'grey': 90,
            'bgred': 41,
            'bggrey': 100
        }
        mapping = {
            'INFO': 'default',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'magenta',
            'DEBUG': 'grey',
            'SUCCESS': 'green'
        }

        color_prefix = '\033['

        def prepare_color(self, color_number):
            return ('%s%dm') % (self.color_prefix, color_number)

        # end def

        def colored(self, record):
            """
            adsasd
            """

            color = self.mapping.get(record.levelname, 'default')
            clr = self.colors[color]

            filepart = record.treadName + ": " if hasattr(record,
                                                          "treadName") and record.treadName != "MainTread" else ""
            filepart += record.name if record.name else ""
            filepart += "." + record.funcName if record.funcName != "<module>" else ""
            formatter = dict(
                all_off=self.prepare_color(0),  # Reset all attributes
                color_on=self.prepare_color(clr),  # Color as given/from lookup
                color_off=self.prepare_color(39),  # Default foreground color
                inverse_on=self.prepare_color(7),  # Reverse (invert the foreground and background colors)
                inverse_off=self.prepare_color(27),  # Reset reverse
                background_off=self.prepare_color(49),  # Default background color
                file_color_on=self.prepare_color(94),  # Light blue
            )
            lines = []
            timestamp = " " + record.asctime if record.asctime else ""
            timestamp_filler = " " * len(timestamp)
            level = "{level:8}".format(level=record.levelname)
            level_filler = "{:{}}".format("", len(level))

            lines_ = record.message.splitlines()
            first_line = True if len(lines_) > 1 else  None
            for line in lines_:
                if first_line is None:  # single line
                    lines.append(
                        "{color_on}{inverse_on}{level}{inverse_off}{color_on}{date}{color_off} {file_color_on}{filepart}:{color_off} {color_on}{message}{color_off}{background_off}{all_off}".format(
                            filepart=filepart, level=level, message=line, date=timestamp, **formatter))
                    break
                elif first_line:  # first line
                    lines.append(
                        "{color_on}{inverse_on}{level}{inverse_off}{color_on}{date}{color_off} {file_color_on}{filepart}:{color_off} {all_off}".format(
                            filepart=filepart, level=level, message=line, date=timestamp, **formatter))
                lines.append(
                    "{color_on}{inverse_on}{level_filler}{inverse_off}{color_off} {color_on}{message}{color_off}{background_off}{all_off}".format(
                        level_filler=level_filler, message=line, date=timestamp, date_filler=timestamp_filler,
                        **formatter))
                first_line = False
            # end for
            return "\n".join(lines)
            # end def

    def __init__(self, date_formatter=None):
        super(ColoredFormatter, self).__init__(datefmt=date_formatter)
        self.color_instance = self.Color(self)

    def colored(self, record):
        return self.color_instance.colored(record)

    # end def


    def format(self, record):
        super(ColoredFormatter, self).format(record)
        # if record.threadName == "MainThread":
        # 	pass
        # part1 = self.firstpart.format(record)
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        else:
            record.asctime = ""
        s = self._fmt % record.__dict__  # py3: s = self.formatMessage(record)
        if record.exc_text:
            if s[-1:] != "\n":
                s += "\n"
            try:
                s = s + record.exc_text
            except UnicodeError:  # PYTHON 2, LOL!
                # Sometimes filenames have non-ASCII chars, which can lead
                # to errors when s is Unicode and record.exc_text is str
                # See issue 8924.
                # We also use replace for when there are multiple
                # encodings, e.g. UTF-8 for the filesystem and latin-1
                # for a script. See issue 13232.
                s = s + record.exc_text.decode(sys.getfilesystemencoding(), 'replace')
        if hasattr(record, "stack_info") and record.stack_info:  # py2 doesn't have .stack_info
            if s[-1:] != "\n":
                s += "\n"
            s = s + record.stack_info  # py3: self.formatStack()
        record.message = s
        return self.colored(record)

    # end def

    def usesTime(self):
        return bool(self.datefmt)
        # end def


# end class


class ColoredStreamHandler(_logging.StreamHandler):
    """
    Like the normal StreamHandler,
    but it automatically sets
    `self.formatter = ColoredFormatter()`
    """

    def __init__(self, stream=None, date_formatter=None):
        super(ColoredStreamHandler, self).__init__(stream)
        self.formatter = ColoredFormatter(date_formatter=date_formatter)


# noinspection PyProtectedMember,PyProtectedMember
class _LoggingWrapper(object):
    SUCCESS = 25  # between WARNING and INFO

    def __init__(self):
        _logging.addLevelName(self.SUCCESS, 'SUCCESS')

    def getLoglevelInt(self, level_string):
        """
        You provide a String, and get a level int
        :param level_string: The level.
        :type  level_string: str
        :return: level
        :rtype : int
        :raises KeyError: if the level does not exists.
        """
        if isinstance(level_string, int):
            return level_string
        # end if
        try:
            return {
                # as names:
                "NOTSET": _logging.NOTSET,
                "DEBUG": _logging.DEBUG,
                "INFO": _logging.INFO,
                "SUCCESS": self.SUCCESS,
                "WARNING": _logging.WARNING,
                "WARN": _logging.WARN,  # = WARNING
                "ERROR": _logging.ERROR,
                "FATAL": _logging.FATAL,  # = CRITICAL
                "CRITICAL": _logging.CRITICAL,
            }[level_string]
        except KeyError:
            try:
                return int(level_string)
            except ValueError:
                pass
            # end try
            raise  # key not known, and is no integer either.
            # end try

    # end def

    def __call__(self, logger_name):
        """
        alias to logger.getLogger(logger_name)
        :param logger_name:
        :return: self.getLogger(logger_name)
        """
        return self.getLogger(logger_name)

    # end def

    def add_colored_handler(self, logger_name=None, stream=None, level=None, date_formatter=None, filter=None):
        """
        Register a logger handler to colorfull print the messages.

        If stream is specified, the instance will use it for logging output; otherwise, sys.stdout will be used.

        If you supply a date_formatter, there will also be printed a date/time for the logged messages.
        Uses python `time.strftime` time formating, see https://docs.python.org/library/time.html#time.strftime

        :keyword logger_name: the name of the logger you want to register the printing to.
                              Probably you should use __name__ , to use your package's logger,
                              "root" will force all loggers to output.
        :type    logger_name: str

        :keyword stream: An output stream. Default: sys.stdout

        :keyword date_formatter: Apply a format for time output. If `None` is given, no time gets printed.
                               Something like "%Y-%m-%d %H:%M:%S". Uses python `time.strftime` time formating,
                               see https://docs.python.org/library/time.html#time.strftime
        :type    date_formatter: str

        :keyword filter: A filter applied to the handler.

        :return: None
        """
        logger = self.getLogger(logger_name)  # __name__
        if stream is None:
            import sys
            stream = sys.stdout
        # end if
        handler = ColoredStreamHandler(stream=stream, date_formatter=date_formatter)
        if filter:
            handler.addFilter(filter)
        # end if
        logger.addHandler(handler)
        if level:
            logger.setLevel(level)
        # end if
        return logger

    # end def

    def test_logger_levels(self, name=__name__, force_all_levels=True):
        logger = self.getLogger(name)
        logger_level = logger.getEffectiveLevel()
        if force_all_levels:
            logger.setLevel(logging.DEBUG)
        logger.debug('level debug')
        logger.info('level info')
        logger.success('level success')
        logger.warning('level warning')
        logger.error('level error')
        logger.critical('level critical')
        if force_all_levels:
            logger.setLevel(logger_level)
            # end if

    # end def

    def getLogger(self, name=None):
        """
        Adds the .success() function to the logger, else it is same as logger.getLogger()
        :param logger: a logging.getLogger() logger.
        :return:
        """
        logger = _logging.getLogger(name)
        logger.SUCCESS = self.SUCCESS
        setattr(logger, "success", lambda message, *args: logger._log(self.SUCCESS, message, args))
        return logger

    if sys.version < "3":
        def success(self, msg, *args, **kwargs):
            """
            Log 'msg % args' with severity 'SUCCESS'.

            To pass exception information, use the keyword argument exc_info with
            a true value.

            logger.debug("Houston, we landed in the %s", "moon", exc_info=False)
            """
            self._success(msg, *args, **kwargs)
    else:
        from .py3 import success

    def _success(self, msg, *args, **kwargs):
        if len(self.root.handlers) == 0:
            self.basicConfig()
        self.root._log(self.SUCCESS, msg, args, **kwargs)

    def __getattr__(self, item):
        if item != "__getattr__":
            if item in self.__dict__:
                return self.__dict__[item]
        if item == "getLogger":
            return self.getLogger
        elif item == "success":
            return self.success
        elif item == "SUCCESS":
            return self.SUCCESS
            # end if
            pass
        else:
            return getattr(_logging, item)
            # end def
# end class


logging = _LoggingWrapper()


class LevelByNameFilter(object):
    def __init__(self, root=logging.WARNING, debug=None, info=None, success=None, warning=None, error=None,
                 critical=None, by_level=None):
        """
        A filter where you specify logging levels bound to names (package names, as known from importing)

        :param root: level the root should have to be logged. None to disable.

        :param debug: all loggers which should log debug and above.
        :param info: all loggers which should log info and above.
        :param success: all loggers which should log success and above.
        :param warning: all loggers which should log warning and above.
        :param error: all loggers which should log error and above.
        :param critical: all loggers which should log critical and above.

        :param by_level: a dict with levels as a key, and names to log as value.
                        Example: {10: "__main__", 20: "a.b.c", 30: ["a.b.d", "a.b.e"], logging.WARNING: "a"}
        """
        self.mapping = dict()
        if root:
            if isinstance(root, str):
                root = logging.getLoglevelInt(root)
            assert isinstance(root, int)
            self.mapping[""] = root
        # end
        level = logging.DEBUG
        self.parse_argument(debug, logging.DEBUG)
        self.parse_argument(info, logging.INFO)
        self.parse_argument(success, logging.SUCCESS)
        self.parse_argument(warning, logging.WARNING)
        self.parse_argument(error, logging.ERROR)
        self.parse_argument(critical, logging.CRITICAL)

        if by_level:
            assert isinstance(by_level, dict)
            for level, files in by_level.items():
                self.parse_argument(files, level)
                # end for
                # end if

    # end def

    def parse_argument(self, argument, level):
        if argument:
            if isinstance(argument, tuple):
                argument = list(argument)
            if not isinstance(argument, list):
                argument = [argument]
            # end if
            assert isinstance(argument, list)
            for part in argument:
                if isinstance(part, (list, tuple)):
                    argument.extend(part)
                elif not isinstance(part, str):
                    raise TypeError("argument {val!r} is type {type}, should be str.".format(val=part, type=type(part)))
                elif "," in part:
                    argument.append(part.split(","))
                else:
                    self.mapping[part.strip() + "."] = level
                    # end if
                    # end for
                    # end if

    # end def

    def filter(self, record):
        if not self.mapping:
            return False  # allow
        # end if

        name = record.name + "."
        mapping_path = ""  # default is "" = root

        for k in self.mapping:
            if name.startswith(k):
                if len(mapping_path) < len(k):  # we got a longer path. longer = more specific.
                    mapping_path = k
                    # end if
                    # end if
        # end for

        if mapping_path in self.mapping:  # e.g. root "" is not specified.
            level = self.mapping[mapping_path]
            return record.levelno >= level
        # end if
        return False
        # end def
# end class