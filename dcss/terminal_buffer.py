from enum import Enum
from collections import namedtuple
import re
import logging

log = logging.getLogger(__name__)


class SequenceType(Enum):
    CURSOR_UP = "A"
    CURSOR_DOWN = "B"
    CURSOR_FORWARD = "C"
    CURSOR_BACK = "D"
    CURSOR_NEXT_LINE = "E"
    CURSOR_PREVIOUS_LINE = "F"
    CURSOR_HORIZONTAL_ABSOLUTE = "G"
    CURSOR_POSITION = "H"
    CURSOR_VERTICAL_ABSOLUTE = "d"
    ERASE_IN_DISPLAY = "J"
    ERASE_IN_LINE = "K"
    ERASE_CHARACTER = "X"
    SCROLL_UP = "S"
    SCROLL_DOWN = "T"
    HORIZONTAL_VERTICAL_POSITION = "f"
    SELECT_GRAPHIC_RENDITION = "m"
    SAVE_CURSOR_POSITION = "s"
    RESTORE_CURSOR_POSITION = "u"
    ENABLE_SETTING = "h"
    DISABLE_SETTING = "l"
    SET_WINDOW = "r"
    UNKNOWN = "ZZZ"


class ParseException(Exception):
    pass


class EscapeSequence():
    # list of escape sequences that use default values of 0
    # instead of the standard of 1
    _default0 = [SequenceType.ERASE_IN_DISPLAY, SequenceType.ERASE_IN_LINE,
                 SequenceType.SELECT_GRAPHIC_RENDITION]
    # list of escape sequences that include an extra '?' in the string
    _hasQMark = [SequenceType.ENABLE_SETTING, SequenceType.DISABLE_SETTING]

    def __init__(self, data, endingLetter, unknownSeq=None):
        self.data = data
        # save a copy in case it's unknown
        self.unknownSequence = unknownSeq
        try:
            self.sequenceType = SequenceType(endingLetter)
        except BaseException:
            # technically, this should have been created using UNKNOWN type
            # assume it can be recreated 'normally'
            self.sequenceType = SequenceType.UNKNOWN
            self.unknownSequence = "\x1b[" + ";".join(
                str(x) for x in self.data) + endingLetter

    def __str__(self):
        # just return the string represnting this sequence
        if self.unknownSequence:
            return self.unknownSequence
        qMark = ""
        if self.sequenceType in EscapeSequence._hasQMark:
            qMark = "?"
        return "\x1b[" + qMark + ";".join(
            str(x) for x in self.data) + self.sequenceType.value

    def __repr__(self):
        return repr(str(self))

    def get_data(self, index):
        # this is just a wrapper to handle default values
        if not isinstance(index, int):
            raise TypeException("index must be an integer")
        if index < len(self.data):
            return self.data[index]
        else:
            # but there are some special cases,
            # because who needs consistency anyways?
            if self.sequenceType in EscapeSequence._default0:
                return 0
            else:
                return 1


class TerminalBuffer():
    _parser = re.compile(r"^\x1b\[\??([\d;]*)(\w)")
    # secondary parser for other sequences that are sufficiently different
    # these commonly don't have data, or don't use nums exclusively for data
    _unknownParser = re.compile(r"^\x1b[\(\)\=\>\%]?([\w\d])?")

    class Position:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Character:
        def __init__(self, value, color):
            self.value = value
            self.color = color

        def __str__(self):
            if self.value:
                return self.value
            return " "

        def reset(self):
            self.value = ""
            self.color = None

    def __init__(self, width=80, height=24, ignoreUnsupported=True):
        self.width = width
        self.height = height
        self.window_top = 0
        self.window_bot = height - 1
        # if we find an escape sequence that's not supported
        # this dictates whether the terminal errors, or silently ignores it
        self.skip_unsupported = ignoreUnsupported

        # this is 'backwards' from normal
        # (i.e. to get the char at x,y you do self.terminal[y][x])
        # the purpose of this is to make pushing full lines up easier
        self.terminal = [
            [self.Character("", None) for _ in range(self.width)]
            for __ in range(self.height)]
        self.cursor_pos = self.Position(0, 0)
        self.savedCursorPosition = self.Position(-1, -1)

        # this represents default coloring,
        # so set it as the current color from the start
        self.cur_color = EscapeSequence([0], "m")

    def __str__(self):
        return self.get_text()

    def parse_sequence(self, string):
        match = TerminalBuffer._parser.match(string)
        if not match:
            match = TerminalBuffer._unknownParser.match(string)

            if not match:
                raise ParseException("Couldn't parse sequence:" + repr(string))

            # just make an unknown sequence
            return EscapeSequence(
                [],
                SequenceType.UNKNOWN.value,
                string[match.start():match.end()]
            ), string[match.end():]

        data, char = match.groups()

        if not data:
            data = []
        else:
            data = [int(x) for x in data.split(';')]

        result = EscapeSequence(data, char), string[match.end():]
        return result

    def get_next_sequence(self, string):
        while string:
            # if the string is an escape sequence,
            # we need to construct the sequence based on the following chars
            if string[0] == '\x1b':
                # parse_sequence handles truncating the string for iteration
                seq, string = self.parse_sequence(string)
                yield seq

            # if the string is a normal string, just yield
            else:
                yield string[0]
                # slice the string for the next iteration
                string = string[1:]

    def input(self, string):
        log_dict = {}
        for val in self.get_next_sequence(string):
            if isinstance(val, EscapeSequence):
                self.apply_sequence(val, log_dict)
            else:
                # handle special case characters
                if val == '\r':
                    self.cursor_pos.x = 0
                elif val == '\b':
                    self.move_cursor(-1, 0, True)
                elif val == '\n':
                    self.move_cursor(0, 1, True)
                elif val == '\x0f' or val == '\x00':
                    pass
                # standard characters
                else:
                    self.terminal[self.cursor_pos.y][self.cursor_pos.x] \
                        = self.Character(val, self.cur_color)
                    self.move_cursor(1, 0, True)

        if len(log_dict):
            log.warning("Ignored sequence counts: " + str(log_dict))

    def get_text(self, x=0, y=0, w=0, h=0, color=False):
        if w == 0:
            w = self.width
        if h == 0:
            h = self.height
        x = max(0, min(self.width - 1, x))
        y = max(0, min(self.height - 1, y))
        w = max(0, min(self.width - x, w))
        h = max(0, min(self.height - y, h))

        return "\n".join("".join(str(self.terminal[i][j]) for j in range(
            x, x + w)) for i in range(y, y + h))

    def move_cursor(self, x, y, wrap):
        if wrap:
            # handles moving 'too far' forward or back
            while self.cursor_pos.x + x >= self.width:
                y += 1
                x -= self.width
            while self.cursor_pos.x + x < 0:
                x += self.width
                y -= 1
        if self.cursor_pos.y + y > self.window_bot:
            self.scroll_up((self.cursor_pos.y + y) - self.window_bot)
            y = (self.cursor_pos.y + y) - (self.window_bot - 1)
        # technically, shouldn't need the max/min functions here
        # but they aren't very expensive, and being safe is cool
        self.cursor_pos.x = max(
            0, min(self.width - 1, self.cursor_pos.x + x))
        self.cursor_pos.y = max(
            0, min(self.height - 1, self.cursor_pos.y + y))

    def clear_terminal(self):
        # this also needs to reset cursor position
        self.cursor_pos.x = 0
        self.cursor_pos.y = 0
        for i in range(len(self.terminal)):
            for k in range(len(self.terminal[i])):
                self.terminal[i][k].reset()

    def clear_from_start(self):
        for i in range(self.cursor_pos.x):
            for j in range(self.cursor_pos.y):
                self.terminal[j][i].reset()

    def clear_to_end(self):
        for i in range(self.cursor_pos.x, self.width):
            for j in range(self.cursor_pos.y, self.height):
                self.terminal[j][i].reset()

    def clear_line_before(self):
        for i in range(self.cursor_pos.x):
            self.terminal[self.cursor_pos.y][i].reset()

    def clear_line_after(self):
        for i in range(self.cursor_pos.x, self.width):
            self.terminal[self.cursor_pos.y][i].reset()

    def clear_line(self):
        for i in range(self.width):
            self.terminal[self.cursor_pos.y][i].reset()

    def scroll_up(self, num):
        for i in range(self.window_top, self.window_bot + 1):
            # we are shifting num lines
            # for any line that's more than num lines from the bottom
            # just copy from the line num lines down
            if i + num <= self.window_bot:
                self.terminal[i] = self.terminal[i + num]
            # if the line is within num lines of the bottom, reset the line
            else:
                self.terminal[i] = \
                    [self.Character("", None) for _ in range(self.width)]

    def scroll_down(self, num):
        # we need to iterate backwards here
        # otherwise, we just copy the first num lines over and over again
        for i in range(self.window_bot, self.window_top + 1, -1):
            # we are shifting num lines
            # for any line that's more than num lines from the bottom
            # just copy from the line num lines down
            if i - num >= self.window_bot:
                self.terminal[i] = self.terminal[i - num]
            # if the line is within num lines of the bottom, reset
            else:
                self.terminal[i] = \
                    [self.Character("", None) for _ in range(self.width)]

    def push_characters_left(self, amount):
        # this is effectively deleting characters
        # and pushing the remaining characters back, due to the removed chars
        # we can just move the characters, overwriting the old values
        for i in range(self.cursor_pos.x, self.width):
            # move characters that aren't being deleted
            if i + amount < self.width:
                self.terminal[self.cursor_pos.y][i] = \
                    self.terminal[self.cursor_pos.y][i + amount]
            # clear characters if the source would be outside the screen
            else:
                self.terminal[self.cursor_pos.y][i] = \
                    self.Character("", None)

    def apply_sequence(self, sequence, log_dict):
        if sequence.sequenceType == SequenceType.CURSOR_UP:
            self.move_cursor(0, -sequence.get_data(0), False)
        elif sequence.sequenceType == SequenceType.CURSOR_DOWN:
            self.move_cursor(0, sequence.get_data(0), False)
        elif sequence.sequenceType == SequenceType.CURSOR_FORWARD:
            self.move_cursor(sequence.get_data(0), 0, False)
        elif sequence.sequenceType == SequenceType.CURSOR_BACK:
            self.move_cursor(-sequence.get_data(0), 0, False)
        elif sequence.sequenceType == SequenceType.CURSOR_NEXT_LINE:
            self.move_cursor(-self.cursor_pos.x,
                             sequence.get_data(0), False)
        elif sequence.sequenceType == SequenceType.CURSOR_PREVIOUS_LINE:
            self.move_cursor(-self.cursor_pos.x, -
                             sequence.get_data(0), False)
        elif sequence.sequenceType == SequenceType.CURSOR_HORIZONTAL_ABSOLUTE:
            self.cursor_pos.x = max(
                0, min(self.width - 1, sequence.get_data(0) - 1))
        elif sequence.sequenceType == SequenceType.CURSOR_VERTICAL_ABSOLUTE:
            self.cursor_pos.y = max(
                0, min(self.height - 1, sequence.get_data(0) - 1))
        elif sequence.sequenceType == \
                SequenceType.HORIZONTAL_VERTICAL_POSITION \
                or sequence.sequenceType == SequenceType.CURSOR_POSITION:
            self.cursor_pos.x = max(
                0, min(self.width - 1, sequence.get_data(1) - 1))
            self.cursor_pos.y = max(
                0, min(self.height - 1, sequence.get_data(0) - 1))
        elif sequence.sequenceType == SequenceType.ERASE_IN_DISPLAY:
            if sequence.get_data(0) == 2:
                self.clear_terminal()
            elif sequence.get_data(0) == 1:
                self.clear_from_start()
            else:
                self.clear_to_end()
        elif sequence.sequenceType == SequenceType.ERASE_IN_LINE:
            if sequence.get_data(0) == 0:
                self.clear_line_after()
            elif sequence.get_data(0) == 1:
                self.clear_line_before()
            else:
                self.clear_line()
        elif sequence.sequenceType == SequenceType.ERASE_CHARACTER:
            self.push_characters_left(sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.SCROLL_UP:
            self.scroll_up(sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.SCROLL_DOWN:
            self.scroll_down(sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.SELECT_GRAPHIC_RENDITION:
            self.cur_color = sequence
        elif sequence.sequenceType == SequenceType.SAVE_CURSOR_POSITION:
            self.savedCursorPosition.x = self.cursor_pos.x
            self.savedCursorPosition.y = self.cursor_pos.y
        elif sequence.sequenceType == SequenceType.RESTORE_CURSOR_POSITION:
            if self.savedCursorPosition.x != -1:
                self.cursor_pos.x = self.savedCursorPosition.x
                self.cursor_pos.y = self.savedCursorPosition.y
        elif sequence.sequenceType == SequenceType.SET_WINDOW:
            if sequence.get_data(0) == 0 and sequence.get_data(1) == 0:
                self.window_top = 0
                self.window_bot = self.height - 1
            else:
                if sequence.get_data(0) - 1 > self.height or\
                        sequence.get_data(0) - 1 < 0 or\
                        sequence.get_data(1) - 1 > self.height or\
                        sequence.get_data(1) < sequence.get_data(0):
                    log.warning("ignoring windowSize: " + repr(sequence))
                else:
                    self.window_top = sequence.get_data(0) - 1
                    self.window_bot = sequence.get_data(1) - 1
        elif self.skip_unsupported:
            if str(sequence) in log_dict.keys():
                log_dict[str(sequence)] += 1
            else:
                log_dict[str(sequence)] = 1
        else:
            raise NotImplementedError(
                "Unsupported sequence: " + repr(sequence))
