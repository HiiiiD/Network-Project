import tkinter as tkt
from tkinterutils import configure_grid, ListBoxPane


class TkinterApplication(tkt.Tk):
    """Entry point of the GUI"""

    def __init__(self, button_send_action):
        super().__init__()
        self.geometry("1000x1000")
        self.title("Chat Network Project")
        configure_grid(self, 2, 3)
        self.__button_send_action = button_send_action
        self.__message_property = tkt.StringVar()
        # Top pane
        self.__top_pane = _TopPane(self)
        self.__top_pane.grid(column=0, row=0, columnspan=2, sticky="nsew")
        # Quiz pane
        self.__quiz_pane = _QuizPane(self, self.__button_send_action, self.__message_property)
        self.__quiz_pane.grid(column=0, row=1, sticky="nsew")
        # Broadcast pane
        self.__broadcast_pane = _BroadcastPane(self)
        self.__broadcast_pane.grid(column=1, row=1, sticky="nsew")
        # Leaderboard pane
        self.__leaderboard_pane = _LeaderboardPane(self)
        self.__leaderboard_pane.grid(column=1, row=2, sticky="nsew")
        self.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __on_closing(self):
        """Function invoked when the window is closed"""
        self.__message_property.set("{quit}")
        self.__button_send_action()

    def set_role(self, new_role: str):
        """Set the role

        Parameters
        ----------
        new_role : str
            New role
        """
        self.__top_pane.set_role(new_role)

    def set_score(self, new_score: int):
        """Set the updated score

        Parameters
        ----------
        new_score : int
            Updated score
        """
        self.__top_pane.set_score(new_score)

    def peek_message(self):
        """Get the current message

        Returns
        -------
        str
            The current message typed by the user
        """
        return self.__message_property.get()

    def reset_field(self):
        """Reset the entry field"""
        self.__message_property.set("")

    def push_client_message(self, msg: str):
        """Push a message into the client listbox

        Parameters
        ----------
        msg : str
            Message to push
        """
        self.__quiz_pane.push_message(msg)

    def push_broadcast_message(self, msg: str):
        """Push a message into the broadcast listbox

        Parameters
        ----------
        msg : str
            Message to push
        """
        self.__broadcast_pane.push_message(msg)

    def push_leaderboard_message(self, msg: str):
        """Push a message into the leaderboard listbox

        Parameters
        ----------
        msg : str
            Message to push
        """
        self.__leaderboard_pane.push_message(msg)

    def clear_leaderboard(self):
        """Clear the leaderboard"""
        self.__leaderboard_pane.flush_listbox()

    def clear_quiz_listbox(self):
        """Clear the quiz listbox"""
        self.__quiz_pane.flush_listbox()

    def disable_inputs(self):
        """Disable the input field and the button"""
        self.__quiz_pane.disable_inputs()


class _TopPane(tkt.Frame):
    """Top pane that contains a role label and a score label"""

    def __init__(self, parent):
        super().__init__(parent)
        configure_grid(self, 2, 1)
        self.__role_label = tkt.Label(self)
        self.__role_label.grid(column=0, row=0, sticky="nsew")
        self.__score_label = tkt.Label(self)
        self.__score_label.grid(column=1, row=0, sticky="nsew")

    def set_score(self, new_score: int):
        """Set the updated score"""
        self.__score_label.config(text=f"Score: {str(new_score)}")

    def set_role(self, new_role: str):
        """Set the role"""
        self.__role_label.config(text=f"Role: {new_role}")


class _CommonAppPane(tkt.Frame):
    """Pane that contains a label and a listbox"""

    def __init__(self, parent, label_str):
        super().__init__(parent)
        self._label = tkt.Label(self)
        self._label.config(text=label_str)
        self._listbox_pane = ListBoxPane(self)

    def push_message(self, msg: str):
        """Push a message to the listbox

        Parameters
        ----------
        msg : str
            Message to push
        """
        self._listbox_pane.listbox.insert(tkt.END, msg)

    def flush_listbox(self):
        """Delete all the elements of the listbox"""
        self._listbox_pane.listbox.delete(0, tkt.END)


class _QuizPane(_CommonAppPane):
    """Pane with the quiz listbox, the text field and the send button"""

    def __init__(self, parent, button_send_action, message_property):
        super().__init__(parent, "Quiz")
        configure_grid(self, 1, 4)
        self._label.grid(column=0, row=0, sticky="nsew")
        self._listbox_pane.grid(column=0, row=1, sticky="nsew")
        self.__entry_field = tkt.Entry(self, textvariable=message_property)
        self.__entry_field.bind("<Return>", button_send_action)
        self.__entry_field.grid(column=0, row=2, sticky="nsew")
        self.__send_button = tkt.Button(self, text="Send", command=button_send_action)
        self.__send_button.grid(column=0, row=3, sticky="nsew")

    def disable_inputs(self):
        """Disable the entry field and the button"""
        self.__entry_field.config(state='disabled')
        self.__send_button.config(state='disabled')


class _BroadcastPane(_CommonAppPane):
    """Pane with the broadcast messages"""

    def __init__(self, parent):
        super().__init__(parent, "Broadcast")
        configure_grid(self, 1, 2)
        self._label.grid(column=0, row=0, sticky="nsew")
        self._listbox_pane.grid(column=0, row=1, sticky="nsew")


class _LeaderboardPane(_CommonAppPane):
    """Pane with the leaderboard"""

    def __init__(self, parent):
        super().__init__(parent, "Leaderboard")
        configure_grid(self, 1, 2)
        self._label.grid(column=0, row=0, sticky="nsew")
        self._listbox_pane.grid(column=0, row=1, sticky="nsew")
