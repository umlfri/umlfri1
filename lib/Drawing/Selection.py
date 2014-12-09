import Connection, Element, ConLabelInfo
from lib.config import config
from lib.Drawing.Context import CDrawingContext

class CSelection:

    def __init__(self):
        self.selected = set()
        '''Set of selected elements, connections or conlabelinfos'''

    def GetSelected(self):
        selected = tuple(self.selected)
        for i in selected:
            if i in self.selected:
                yield i

    def GetSelectedSet(self):
        '''
        Return set of selected objects.
        @return: set of selected objects
        '''
        return self.selected

    def GetSelectedElements(self, nolabels = False):
        for i in self.selected:
            if nolabels:
                if isinstance(i, Element.CElement):
                    yield i
            else:
                if isinstance(i, (Element.CElement, ConLabelInfo.CConLabelInfo)):
                    yield i

    def GetSelectedConnections(self):
        for i in self.selected:
            if isinstance(i, Connection.CConnection):
                yield i

    def __GetSquares(self, selElement):
        '''
        Create squares and return it as list.
        :param selElement:
        :return:
        '''
        x, y = selElement.GetPosition()
        context = CDrawingContext(selElement, (x + 0, y + 0))
        rx, ry = selElement.GetObject().GetType().GetResizable(context)
        w, h = selElement.GetSize()
        squares = []

        if rx and ry:
            squares.append(self.__CreateSquare(x       , y       ,  1,  1))
            squares.append(self.__CreateSquare(x + w   , y       , -1,  1))
            squares.append(self.__CreateSquare(x       , y + h   ,  1, -1))
            squares.append(self.__CreateSquare(x + w   , y + h   , -1, -1))
        if ry:
            squares.append(self.__CreateSquare(x + w//2, y       ,  0,  1))
            squares.append(self.__CreateSquare(x + w//2, y + h   ,  0, -1))
        if rx:
            squares.append(self.__CreateSquare( x      , y + h//2,  1,  0))
            squares.append(self.__CreateSquare(x + w   , y + h//2, -1,  0))

        return squares

    def __CreateSquare(self, x, y, posx, posy):
        '''
        Creates new square and return it.
        :param x:
        :param y:
        :param posx:
        :param posy:
        :return:
        '''
        size = config['/Styles/Selection/PointsSize']
        if posx == 0:
            x = x - size // 2
            x1 = x + size
        else:
            x1 = x + posx * size
        if posy == 0:
            y = y - size // 2
            y1 = y + size
        else:
            y1 = y + posy * size
        if x1 < x:
            x1, x = x, x1
        if y1 < y:
            y1, y = y, y1

        return (((-posx, -posy), (x, y), (x1 - x, y1 - y)))

    def GetSquareAtPosition(self, pos):
        '''
        Checks if pos is located in allowed squares. There may be 8 squares.
        4 squares are in corners and next 4 squares are in half of edges.
        It's assumed, then is selected only one element.
        :param pos: position of click
        :return: position of square
        '''
        selElement = list(self.GetSelectedElements())[0]

        if isinstance(selElement, Element.CElement):
            squares = self.__GetSquares(selElement)
            x, y = pos
            for sq in squares:
                sqbx = sq[1][0]
                sqby = sq[1][1]
                sqex = sqbx + sq[2][0]
                sqey = sqby + sq[2][1]
                if (x >= sqbx and x <= sqex and y >= sqby and y <= sqey):
                    return sq[0]

    def SelectedCount(self):
        return len(self.selected)

    def AddToSelection(self, element):
        self.selected.add(element)

    def RemoveFromSelection(self, element):
        self.selected.remove(element)

    def DeselectAll(self):
        self.selected = set()

    def SelectAll(self, elements, connections):
        for e in elements:
            self.selected.add(e)

        for c in connections:
            self.selected.add(c)

    def __IsSelected(self, selObj):
        '''
        Checks if selObj is selected.
        @param selObj: CSelectableObject
        @return: bool
        '''
        for i in self.selected:
            if i is selObj:
                return True
            if isinstance(i, ConLabelInfo.CConLabelInfo) and i.GetConnection() is selObj:
                return True

        return False

    def PaintSelection(self, canvas, selObj, delta = (0, 0)):
        '''
        Draws selection for selObj, if selObj is located in self.selected.

        @param canvas:
        @param selObj: instance of CEelement, CConnection or CConLabelInfo
        @param delta:
        '''
        if self.__IsSelected(selObj):

            if isinstance(selObj, Element.CElement):
                x, y = selObj.GetPosition()
                context = CDrawingContext(selObj, (x + delta[0], y + delta[1]))
                rx, ry = selObj.GetObject().GetType().GetResizable(context)

                minsize = selObj.GetMinimalSize()

                # calculate actual size from delta size, if loaded older version of project (1.1.0)
                if selObj.hasDeltaSize:
                    selObj.hasDeltaSize = False
                    selObj.actualSize = ( minsize[0] + selObj.actualSize[0], minsize[1] + selObj.actualSize[1] )

                w, h = selObj.GetSize()
                wasSmall = False
                if w < minsize[0]:
                    w = minsize[0]
                    wasSmall = True
                if h < minsize[1]:
                    h = minsize[1]
                    wasSmall = True
                if wasSmall:
                    selObj.SetSize((w, h))

                dx, dy = delta
                
                # squares are painted, if exactly one element is selected
                if len(list(self.GetSelectedElements())) == 1:
                    self.__DrawElementSquares(canvas, dx, dy, list(self.GetSelectedElements())[0])

                canvas.DrawRectangle((x + dx, y + dy), (w, h), fg = config['/Styles/Selection/RectangleColor'], line_width = config['/Styles/Selection/RectangleWidth'])
            elif isinstance(selObj, Connection.CConnection):
                size = config['/Styles/Selection/PointsSize']
                color = config['/Styles/Selection/PointsColor']
                selColor = config['/Styles/Selection/RectangleColor']
                dx, dy = delta
                for index, i in enumerate(selObj.GetPoints()):
                    canvas.DrawRectangle((i[0] + dx - size//2, i[1] + dy - size//2), (size, size), color)
                for label in selObj.labels.values():
                    if self.__IsSelected(label):
                        canvas.DrawRectangle(label.GetPosition(), label.GetSize(), selColor)
                    else:
                        canvas.DrawRectangle(label.GetPosition(), label.GetSize(), color)

    def __DrawElementSquares(self, canvas, dx, dy, selElement):
        for i in self.__GetSquares(selElement):
            canvas.DrawRectangle((i[1][0] + dx, i[1][1] + dy), i[2], None, config['/Styles/Selection/PointsColor'])
