import json
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, QMimeData
from PySide6.QtGui import QStandardItemModel, QStandardItem

class MenuModel(QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []

    def load_from_json(self, file_path):
        self.clear()
        self.items = []
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        for category in data['categories']:
            category_item = QStandardItem(category['name'])
            category_item.setSelectable(False)
            category_item.setDropEnabled(False)
            self.appendRow(category_item)
            for item in category['items']:
                self.items.append(item)
                name_item = QStandardItem(f"{len(self.items)}. {item['name']}")
                self.appendRow(name_item)

    def save_to_json(self, file_path):
        data = {"categories": []}
        current_category = None
        for i in range(self.rowCount()):
            item = self.item(i)
            if not item.isSelectable(): # It's a category
                current_category = {"name": item.text(), "items": []}
                data["categories"].append(current_category)
            else:
                name = item.text()
                name = ".".join(name.split(".")[1:]).strip()
                command = self.items[i-1]["command"]
                menu_item = {"name": name, "command": command}
                if current_category is not None:
                    current_category["items"].append(menu_item)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def add_item(self, index, name, command):
        self.items.append({"name": name, "command": command})
        self.insertRow(index.row() + 1, QStandardItem(f"{len(self.items)}. {name}"))
        self.save_to_json("/home/herb/Desktop/MasterMenu/menu.json")

    def edit_item(self, index, name, command):
        item_number = int(self.itemFromIndex(index).text().split(".")[0])
        self.items[item_number - 1] = {"name": name, "command": command}
        self.itemFromIndex(index).setText(f"{item_number}. {name}")
        self.save_to_json("/home/herb/Desktop/MasterMenu/menu.json")

    def delete_item(self, index):
        self.removeRow(index.row())
        self.save_to_json("/home/herb/Desktop/MasterMenu/menu.json")

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsDropEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            return False

        if action == Qt.IgnoreAction:
            return True

        if column > 0:
            return False

        if not parent.isValid():
            return False

        parent_item = self.itemFromIndex(parent)
        if not parent_item:
            return False

        # If the drop is on an item, we want to drop it on the category
        if parent_item.parent():
            parent_item = parent_item.parent()
            parent = parent_item.index()

        source_rows = []
        encoded_data = data.data('application/x-qabstractitemmodeldatalist')
        stream = QDataStream(encoded_data, QIODevice.ReadOnly)
        while not stream.atEnd():
            r, c, d = stream.readInt32(), stream.readInt32(), stream.readInt32()
            source_rows.append(r)

        source_items = []
        for r in sorted(source_rows, reverse=True):
            source_items.insert(0, self.takeRow(r))

        for items in source_items:
            parent_item.appendRow(items)

        self.save_to_json("/home/herb/Desktop/MasterMenu/menu.json")
        return True

    def save_to_json(self, file_path):
        data = {"categories": []}
        for i in range(self.rowCount()):
            category_item = self.item(i)
            category = {"name": category_item.text(), "items": []}
            for j in range(category_item.rowCount()):
                name = category_item.child(j, 0).text()
                # remove number from name
                name = ".".join(name.split(".")[1:]).strip()
                command = category_item.child(j, 1).text()
                item = {"name": name, "command": command}
                category["items"].append(item)
            data["categories"].append(category)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)