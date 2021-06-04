import tkinter as tkt


def configure_grid(node: tkt.Misc, colnum: int, rownum: int):
    """Configures a grid with `colnum` columns and `rownum` rows

    Parameters
    ----------
    node : tkinter.BaseWidget
        The container node that needs to have a grid layout
    colnum : int
        The number of columns of the grid
    rownum : int
        The number of rows of the grid
    """
    for i in range(colnum):
        node.grid_columnconfigure(i, weight=1)

    for i in range(rownum):
        node.grid_rowconfigure(i, weight=1)


def build_scrollable_listbox(parent: tkt.Misc):
    """Build a  with a vertical scrollbar

    Parameters
    ----------
    parent : tkt.Misc
        Parent node of the listbox

    Returns
    -------
    tkinter.Listbox
        Listbox with a scrollbar that scrolls on the Y and X axis
    """
    vertical_scrollbar = tkt.Scrollbar(parent)
    horizontal_scrollbar = tkt.Scrollbar(parent, orient=tkt.HORIZONTAL)
    listbox = tkt.Listbox(parent, yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
    vertical_scrollbar.pack(side=tkt.RIGHT, fill=tkt.Y)
    horizontal_scrollbar.pack(side=tkt.BOTTOM, fill=tkt.X)
    listbox.pack(side=tkt.LEFT, expand=True, fill=tkt.BOTH)

    return listbox


class ListBoxPane(tkt.Frame):
    """Pane that contains a listbox with a vertical and horizontal scrollbar"""

    def __init__(self, parent):
        super().__init__(parent)
        configure_grid(self, 1, 1)
        self.listbox = tkt.Listbox(self)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        self.grid_propagate(False)

        vertical_scrollbar = tkt.Scrollbar(self, orient=tkt.HORIZONTAL)
        vertical_scrollbar.config(command=self.listbox.xview)
        vertical_scrollbar.grid(row=1, column=0, sticky="ew")
        self.listbox.config(xscrollcommand=vertical_scrollbar.set)
        horizontal_scrollbar = tkt.Scrollbar(self, orient=tkt.VERTICAL)
        horizontal_scrollbar.config(command=self.listbox.yview)
        horizontal_scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=horizontal_scrollbar.set)
        # Message list
        #self.listbox = build_scrollable_listbox(self)
