
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QPainter, QFont
from PySide6.QtCore import Qt

class MenuDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        # Get the item data
        item = index.model().itemFromIndex(index)

        # Set the font
        font = QFont("Serif", 12)
        if item.parent() is None:
            # It's a category
            font.setBold(True)
            font.setPixelSize(24)
        else:
            # It's an item
            font.setPixelSize(18)

        painter.setFont(font)

        # Draw the text
        painter.drawText(option.rect, Qt.AlignLeft | Qt.AlignVCenter, item.text())

        painter.restore()
