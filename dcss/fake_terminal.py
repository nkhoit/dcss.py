from enum import Enum
from collections import namedtuple


class SequenceType(Enum):
    CURSOR_UP = "A"
    CURSOR_DOWN = "B"
    CURSOR_FORWARD = "C"
    CURSOR_BACK = "D"
    CURSOR_NEXT_LINE = "E"
    CURSOR_PREVIOUS_LINE = "F"
    CURSOR_HORIZONTAL_ABSOLUTE = "G"
    CURSOR_POSITION = "H"
    ERASE_IN_DISPLAY = "J"
    ERASE_IN_LINE = "K"
    SCROLL_UP = "S"
    SCROLL_DOWN = "T"
    HORIZONTAL_VERTICAL_POSITION = "f"
    SELECT_GRAPHIC_RENDITION = "m"
    SAVE_CURSOR_POSITION = "s"
    RESTORE_CURSOR_POSITION = "u"


class ParseException(Exception):
    pass


class EscapeSequence():
    def __init__(self, data, endingLetter):
        self.data = data
        # save a copy in case it's unknown
        try:
            self.sequenceType = SequenceType(endingLetter)
        except:
            raise TypeError(
                    "Unsupported EscapeSequence, ending with: " + endingLetter)

    def get_string(self):
        # just return the string represnting this sequence
        return "\033[" + ";".join(
                str(x) for x in self.data) + self.sequenceType.value

    def get_data(self, index):
        # this is just a wrapper to handle the logic of defaulting to 1
        if not isinstance(index, int):
            raise TypeException("index must be an integer")
        if index < len(self.data):
            return self.data[index]
        else:
            # but there are some special cases,
            # because who needs consistency anyways?
            if self.sequenceType == SequenceType.ERASE_IN_DISPLAY \
                    or self.sequenceType == SequenceType.ERASE_IN_LINE \
                    or self.sequenceType == SequenceType.SELECT_GRAPHIC_RENDITION:
                return 0
            else:
                return 1


class FakeTerminal():
    Position = namedtuple("Position", "x y")
    Character = namedtuple("Character", "value color")

    def __init__(self, width=80, height=24):
        self.width = width
        self.height = height

        # this is 'backwards' from normal
        # (i.e. to get the char at x,y you do self.terminal[y][x])
        # the purpose of this is to make pushing full lines up easier
        self.terminal = [[None] * width] * height
        self.cursorPosition = self.Position(x=0, y=0)
        self.savedCursorPosition = self.Position(x=-1, y=-1)

        # this represents default coloring,
        # so set it as the current color from the start
        self.currentColor = EscapeSequence(0, "m")

    def get_next_sequence(self, string):
        for i in range(len(string)):

            # if the string is an escape sequence,
            # we need to construct the sequence based on the following chars
            if string[i] == '\033':
                dataVals = []
                done = False

                i += 1
                char = string[i]
                if char != '[':
                    # dunno what to do, panic!
                    raise ParseException("Couldn't parse the character sequence at index(" + str(i-1) + " from string: " + string)

                while not done:
                    i += 1

                    # this char will either be data, or the end of the string
                    data = ""
                    char = string[i]

                    # if this character is a digit,
                    # then parse until no more digits
                    while char.isdigit() or char == ";":
                        # character means we are done with the current number
                        # input, and are ready for the next input value
                        if char == ";":
                            if len(data) != 0:
                                dataVals.append(int(data))
                                data = ""
                            # it is valid to omit a number
                            # (which defaults it to 1),
                            # and then immediately have a ;
                            # to signify the second number is starting
                            # so, when we don't have a data length, default it
                            else:
                                dataVals.append(1)
                        # number means we just keep building the data value
                        else:
                            data += char

                        # finally, prep the loop for
                        # next iteration, then continue
                        i += 1
                        char = string[i]

                    yield EscapeSequence(dataVals, char)

            # if the string is a normal string, just yield
            else:
                yield string[i]

    def input_string(self, string):
        for val in self.get_next_sequence(string):
            if isinstance(val, EscapeSequence):
                self.apply_sequence(val)
            else:
                self.terminal[self.cursorPosition.y][self.cursorPosition.x] \
                        = self.Character(value=val, color=self.currentColor)

    def get_just_characters(self, x=0, y=0, w=0, h=0):
        if w == 0:
            w = self.width
        if h == 0:
            h = self.height
        x = max(0, min(self.width, x))
        y = max(0, min(self.height, y))
        w = max(0, min(self.width - x, w))
        h = max(0, min(self.height - y, h))

        result = []
        for i in range(y, h):
            result.append("")
            for j in range(x, w):
                result[-1] += self.terminal[j][i].value

        return result

    def get_full_text(self, x=0, y=0, w=0, h=0):
        if w == 0:
            w = self.width
        if h == 0:
            h = self.height
        x = max(0, min(self.width, x))
        y = max(0, min(self.height, y))
        w = max(0, min(self.width - x, w))
        h = max(0, min(self.height - y, h))

        result = []
        for i in range(y, h):
            result.append("")
            for j in range(x, w):
                result[-1] += self.terminal[j][i].color
                result[-1] += self.terminal[j][i].value

        return result

    def move_cursor(self, x, y):
        self.cursorPosition.x = max(
                0, min(self.width, self.cursorPosition.x + x))
        self.cursorPosition.y = max(
                0, min(self.height, self.cursorPosition.y + y))

    def clear_terminal(self):
        for i in len(self.terminal):
            for k in len(self.terminal[i]):
                self.terminal[i][k] = None

    def clear_line_before(self):
        for i in range(self.cursorPosition.x):
            self.terminal[self.cursorPosition.y][i] = None

    def clear_line_after(self):
        for i in range(self.cursorPosition, self.width):
            self.terminal[self.cursorPosition.y][i] = None

    def clear_line(self):
        for i in range(self.width):
            self.terminal[self.cursorPosition.y][i] = None

    def apply_sequence(self, sequence):
        if sequence.sequenceType == SequenceType.CURSOR_UP:
            self.move_cursor(0, -sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.CURSOR_DOWN:
            self.move_cursor(0, sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.CURSOR_FORWARD:
            self.move_cursor(sequence.get_data(0), 0)
        elif sequence.sequenceType == SequenceType.CURSOR_BACK:
            self.move_cursor(-sequence.get_data(0), 0)
        elif sequence.sequenceType == SequenceType.CURSOR_NEXT_LINE:
            self.move_cursor(-self.cursorPosition.x, sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.CURSOR_PREVIOUS_LINE:
            self.move_cursor(-self.cursorPosition.x, -sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.CURSOR_HORIZONTAL_ABSOLUTE:
            self.cursorPosition.x = max(
                    0, min(self.width, sequence.get_data(0)))
        elif sequence.sequenceType == SequenceType.CURSOR_POSITION \
                or sequence.sequenceType == SequenceType.HORIZONTAL_VERTICAL_POSITION:
            self.cursorPosition.x = max(
                    0, min(self.width, sequence.get_data(0)))
            self.cursorPosition.y = max(
                    0, min(self.height, sequence.get_data(1)))
        elif sequence.sequenceType == SequenceType.ERASE_IN_DISPLAY:
            if sequence.get_data(0) == 2:
                self.clear_terminal()
            else:
                raise NotImplementedError("currenly only supports erasing full display")
        elif sequence.sequenceType == SequenceType.ERASE_IN_LINE:
            if sequence.get_data(0) == 0:
                self.clear_line_after()
            elif sequence.get_data(0) == 1:
                self.clear_line_before()
            else:
                self.clear_line()
        elif sequence.sequenceType == SequenceType.SCROLL_UP:
            self.scrollUp(sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.SCROLL_DOWN:
            self.scrollDown(sequence.get_data(0))
        elif sequence.sequenceType == SequenceType.SELECT_GRAPHIC_RENDITION:
            raise NotImplementedError("too lazy tonight")
        elif sequence.sequenceType == SequenceType.SAVE_CURSOR_POSITION:
            self.savedCursorPosition.x = self.cursorPosition.x
            self.savedCursorPosition.y = self.cursorPosition.y
        elif sequence.sequenceType == SequenceType.RESTORE_CURSOR_POSITION:
            if self.savedCursorPosition.x != -1:
                self.cursorPosition.x = self.savedCursorPosition.x
                self.cursorPosition.y = self.savedCursorPosition.y


def test():
    return FakeTerminal(), open("test.txt", "r")
