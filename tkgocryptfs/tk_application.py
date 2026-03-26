"""
class module for tkgocryptfs
"""
import os
import subprocess
import shlex
import pexpect

from pathlib import Path
from tkinter import *
from tkinter import filedialog

from tkgocryptfs.functions import *

import logging

# Per-module logger
logger = logging.getLogger(__name__)

button_width = 20
favicon_name = 'favicon.gif'
default_ram_dir = "/run/user"
text_show="show"
text_hide="hide"

class AppT:
    """
    The gui class
    """

    def __init__(self) -> None:
        userpath = os.path.expanduser("~")  # check what user
        configdir = userpath + "/.tkgocryptfs"
        if not os.access(configdir, os.F_OK):  # check if user has a directory containing persistent usr
            os.mkdir(configdir)  # if not create the directory
        configfile = "conf"
        # path to config file
        self.path_to_config = configdir + "/" + configfile
        logging.debug("Config file " + self.path_to_config)
        if not os.access(self.path_to_config, os.F_OK):  # check if file exists containing persistent usr
            os.system("touch " + self.path_to_config)  # if not create the empty file
        path_to_config_file = open(
            self.path_to_config)  # now read the file containing persistent usr or being empty
        paths_to_gocryptfs = path_to_config_file.readlines()
        path_to_config_file.close()

        # select and create mounting point in ram
        uid = os.getuid()
        self.mounting_point = default_ram_dir + "/" + str(uid) + "/tkgocryptfs/"
        p_temp_dir = Path(self.mounting_point)
        if not p_temp_dir.is_dir():
            p_temp_dir.mkdir(parents=True, exist_ok=True)

        # since the list box does not point to anything the last position is taken
        self.index = '0'

        # Track if the open windows is open to not open additional windows
        self.init_window = None
        self.change_password_window = None

        # set up the gui stuff
        self.window = Tk()
        self.window.title('Gui for gocryptfs')

        # variables from other windows that must be available outside the window methode
        self.init_password1 = StringVar()
        self.init_password2 = StringVar()
        self.change_password1 = StringVar()
        self.change_password2 = StringVar()

        # add an icon
        assets_dir = os.path.dirname(os.path.abspath(__file__)) + "/assets" + os.sep
        favicon = assets_dir + favicon_name
        img = PhotoImage(file=favicon)
        self.window.call("wm", "iconphoto", self.window, "-default", img)
        self.window.resizable(width=FALSE, height=FALSE)

        # create the menus
        self.menubar = Menu(self.window)
        file_menu = Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Add new directory to the list", command=self.add_crypt_dir_to_list)
        file_menu.add_command(label="Initialize crypted directory", command=self.init_crypt_dir)
        file_menu.add_command(label="Remove directory from list", command=self.remove_crypt_dir_from_list)
        file_menu.add_separator()
        file_menu.add_command(label="Change Password", command=self.change_password)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)
        self.menubar.add_command(label="About", command=about)
        self.window.config(menu=self.menubar)

        row = 0
        # add the password label and entry field
        self.label = Label(self.window, text='Password')
        self.label.grid(row=row,columnspan=2)

        row += 1
        self.password = Entry(self.window, show='*')
        self.password.grid(row=row)
        self.password_button = Button(master=self.window, text=text_show, width=10,
                                      command=self.show_password)
        self.password_button.grid(row=row, column=1)

        # add the path label and value
        row += 1
        self.label_path = Label(self.window, text='Path to the crypt directory')
        self.label_path.grid(row=row,columnspan=2)
        self.dir_gui = StringVar()

        row += 1
        self.path_label = Label(master=self.window, textvariable=self.dir_gui)
        self.path_label.grid(row=row,columnspan=2)

        row += 1
        self.mounted_gui = StringVar()
        self.mounted_label = Label(master=self.window, textvariable=self.mounted_gui)
        self.mounted_label.grid(row=row,columnspan=2)

        # set up and register the buttons
        row += 1
        self.mount_button = Button(master=self.window, text='Mount gocryptfs', width=button_width,
                                   command=self.encrypted_fs_mount)
        self.mount_button.grid(row=row,columnspan=2)

        row += 1
        self.umount_button = Button(master=self.window, text='Umount gocryptfs', width=button_width,
                                    command=self.encrypted_fs_umount)
        self.umount_button.grid(row=row,columnspan=2)

        row += 1
        self.open_button = Button(master=self.window, text='Open gocryptfs', width=button_width,
                                  command=self.encrypted_fs_open)
        self.open_button.grid(row=row,columnspan=2)

        # set up the listbox and its label
        row += 1
        self.listbox = Listbox(self.window, width=50, height=5, justify='center')
        self.listbox.bind('<<ListboxSelect>>', self.listbox_change)
        self.listbox.grid(row=row, columnspan=2)
        for item in paths_to_gocryptfs:
            i = item.strip()
            if len(i) > 0:
                self.listbox.insert(END, i)
        self.listbox.select_set(0)  # selects the first one, so something is selected
        self.dir_gui.set(self.listbox.get(0))
        self.path_to_gocryptfs = self.listbox.get(0)
        self.update_gui()

    def run(self) -> None:
        """
        run the gui application
        :return:
        """
        self.window.mainloop()

    def show_password(self)-> None:
        """
        Show or hide the password
        :return: None
        """
        if    self.password_button["text"] == text_hide:
            self.password.config(show="*")
            self.password_button["text"]=text_show
        else:
            self.password.config(show="")
            self.password_button["text"] = text_hide

    def is_mounted(self) -> bool:
        """
        return if it is mounted
        :return: true when mounted
        """
        return os.path.ismount(self.mounting_point)

    def update_gui(self) -> None:
        """
        update the gui and show status of the buttons
        :return: None
        """
        if self.is_mounted():
            self.mounted_gui.set("Mounted")
            self.mount_button.config(relief="sunken")
            self.umount_button.config(relief="raised")
            self.open_button.config(relief="raised")
        else:
            self.mounted_gui.set("Not Mounted")
            self.mount_button.config(relief="raised")
            self.umount_button.config(relief="raised")
            self.open_button.config(relief="raised")

    def listbox_change(self, evt) -> None:
        """
        Event handler click on listbox, moves clicked one on top of the list to have recently selected in the future
        :param evt: tkinter event
        :return: None
        """
        w = evt.widget
        try:
            index = int(w.curselection()[0])
        except IndexError:
            logger.debug("listbox change exception")
            logger.debug(w.curselection())
            index = 0
        if index != 0:  # clicked on to be on top of the list
            directory_name = self.listbox.get(index)
            self.listbox.delete(ANCHOR)
            self.listbox.insert(0, directory_name)
            self.update_config()
        self.dir_gui.set(self.listbox.get(0))
        self.path_to_gocryptfs = self.listbox.get(0)
        self.update_gui()

    def quit(self) -> None:
        """
        button event to quit the application
        :return:
        """
        self.window.destroy()

    def update_config(self) -> None:
        """
        updates the config file by re-creating it
        :return: None
        """
        items = self.listbox.get(0, END)
        path_to_config_file = open(self.path_to_config, 'w')  # now write the file containing persistent usr
        for i in items:
            path_to_config_file.write(i + "\n")
        path_to_config_file.close()

    def exist_config(self, n: str) -> bool:
        """
        Check if directory exists already
        :param n:
        :return:
        """
        items = self.listbox.get(0, END)
        value = False
        for i in items:
            if i == n:
                value = True
        return value

    def add_crypt_dir_to_list(self) -> None:
        """
        Adds new directory to the list
        :return: None
        """
        directory_name = filedialog.askdirectory(initialdir='~')
        if self.exist_config(directory_name):
            messagebox.showinfo("Info", "Directory " + directory_name + " already exists in the list")
        elif len(directory_name) > 0:
            if not os.path.isdir(directory_name):
                messagebox.showinfo("Info", "Directory " + directory_name + " does not exist and will be created")
                os.mkdir(directory_name)
            self.listbox.insert(0, directory_name)
            self.update_config()

    def remove_crypt_dir_from_list(self) -> None:
        """
        Removes directory from the list
        :return:
        """
        self.listbox.delete(ANCHOR)
        self.update_config()

    def encrypted_fs_umount(self) -> None:
        """
        Un-mounts the encrypted directory
        :return: None
        """
        cmd = "fusermount -u " + self.mounting_point
        logger.debug(cmd)
        args_cmd = shlex.split(cmd)
        p = subprocess.Popen(args_cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,  # standard err are passed to stdout
                             )  # open new process
        stdout_value, stderr_value = p.communicate()  # communicate is a one time action, afterward p is closed
        if stdout_value == b'':
            messagebox.showinfo("umount", f"Successfully unmounted\n{self.path_to_gocryptfs}")
        else:
            messagebox.showinfo("umount", f"{stdout_value.decode()}")
        self.update_gui()

    def encrypted_fs_mount(self) -> None:
        """
        Mounts the encrypted directory
        :return: None
        """
        if not self.is_mounted():
            password = self.password.get()
            cmd = "gocryptfs " + self.path_to_gocryptfs + " " + self.mounting_point
            logger.debug(cmd)
            child = pexpect.spawn(cmd)
            try:
                child.expect("Password:", timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))
            child.sendline(password)
            try:
                child.expect(pexpect.EOF, timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))
            output = child.before.decode()
            clean_output = remove_esc(output)
            messagebox.showinfo("Info", clean_output)
            self.update_gui()
            self.encrypted_fs_open()  # open file manager
        else:
            messagebox.showinfo("mount", self.path_to_gocryptfs + "/crypt is already mounted")

    def encrypted_fs_open(self) -> None:
        """
        opens the encrypted directory
        :return: None
        """
        if self.is_mounted():
            cmd = "xdg-open " + self.mounting_point
            os.system(cmd)

    def show_master_key_window(self, s: str) -> None:
        """
        Show master key in a way it can be cut and pasted
        :param s: text containing master key
        :return: None
        """
        master_key_window = Toplevel(self.window)
        master_key_window.title("Info crypt directory")
        master_key_window.geometry("600x200")
        row = 0
        text = Text(master_key_window,
                    width=400,
                    height=20,
                    highlightthickness=0,
                    bd=0,
                    bg='white',
                    relief='sunken',
                    padx=5,
                    pady=5)
        text.grid(row=row, sticky=W)
        text.insert("end", s)

    def change_password(self) -> None:
        """
        change the password
        :return: None
        """
        if not self.is_mounted():
            if self.change_password_window is None or not Toplevel.winfo_exists(self.change_password_window):
                self.window.iconify()
                self.change_password_window = Toplevel(self.window)
                self.change_password_window.title("Change password")
                self.change_password_window.geometry("450x100")
                row = 0
                # show what dir is selected
                password_dir_text = Label(self.change_password_window, text='Selected directory', width=20,
                                          anchor="w")
                password_dir_text.grid(column=0, row=0, sticky=W)
                password_dir_value = Label(self.change_password_window, text=self.path_to_gocryptfs, width=40,
                                           anchor="w")
                password_dir_value.grid(column=1, row=row, sticky=W)

                # setup password entry variable
                row += 1
                password_label_1 = Label(self.change_password_window, text='New Password', width=20, anchor="w")
                password_label_1.grid(column=0, row=row, sticky=W)
                # setup password entry
                pass1 = Entry(master=self.change_password_window,
                              textvariable=self.change_password1, show='*', width=40)
                pass1.grid(column=1, row=row)

                # setup password entry variable for confirmation
                row += 1
                password_label_2 = Label(self.change_password_window, text='Verify Password', width=20, anchor="w")
                password_label_2.grid(column=0, row=row, sticky=W)
                # setup password entry for confirmation
                pass2 = Entry(master=self.change_password_window,
                              textvariable=self.change_password2, show='*', width=40)
                pass2.grid(column=1, row=row)

                # set up the ok button
                row += 1
                ok_button = Button(master=self.change_password_window,
                                   text='Ok',
                                   width=20,
                                   command=self.ok_change_password_window)
                ok_button.grid(column=1,
                               row=row,
                               sticky=W)
                # set up the cancel button
                cancel_button = Button(master=self.change_password_window,
                                       text='Cancel',
                                       width=20,
                                       command=self.change_password_window_close)
                cancel_button.grid(column=0,
                                   row=row,
                                   sticky=W)
                # Reset reference when child is closed
                self.change_password_window.protocol("WM_DELETE_WINDOW", self.change_password_window_close)
        else:
            messagebox.showerror("Error", "Crypted directory is mounted, unmount it")

    def change_password_window_close(self):
        """Reset reference when the child window is closed."""
        if self.change_password_window is not None:
            self.change_password_window.destroy()
            self.change_password_window = None
            self.window.deiconify()

    def init_crypt_dir(self) -> None:
        """
        initialize crypt dir by adding config and password
        :param self:
        :return:
        """
        if not os.path.isdir(self.path_to_gocryptfs):
            messagebox.showinfo("Info", "Directory " + self.path_to_gocryptfs + " not found and will be created")
            os.mkdir(self.path_to_gocryptfs)
        if len(os.listdir(self.path_to_gocryptfs)) > 0:
            messagebox.showinfo("Error", "Crypted directory is not empty")
        else:
            if self.init_window is None or not Toplevel.winfo_exists(self.init_window):
                self.window.iconify()
                self.init_window = Toplevel(self.window)
                self.init_window.title("Initialize crypt directory")
                self.init_window.geometry("450x100")
                row = 0
                # show what dir is selected
                password_dir_text = Label(self.init_window, text='Selected directory', width=20, anchor="w")
                password_dir_text.grid(column=0, row=0, sticky=W)
                password_dir_value = Label(self.init_window, text=self.path_to_gocryptfs, width=40, anchor="w")
                password_dir_value.grid(column=1, row=row, sticky=W)

                # setup password entry variable
                row += 1
                password_label_1 = Label(self.init_window, text='New Password', width=20, anchor="w")
                password_label_1.grid(column=0, row=row, sticky=W)
                # setup password entry
                pass1 = Entry(master=self.init_window,
                              textvariable=self.init_password1, show='*', width=40)
                pass1.grid(column=1, row=row)

                # setup password entry variable for confirmation
                row += 1
                password_label_2 = Label(self.init_window, text='Verify Password', width=20, anchor="w")
                password_label_2.grid(column=0, row=row, sticky=W)
                # setup password entry for confirmation
                pass2 = Entry(master=self.init_window,
                              textvariable=self.init_password2, show='*', width=40)
                pass2.grid(column=1, row=row)

                # set up the ok button
                row += 1
                ok_button = Button(master=self.init_window,
                                   text='Ok',
                                   width=20,
                                   command=self.ok_init_window)
                ok_button.grid(column=1,
                               row=row,
                               sticky=W)
                # set up the cancel button
                cancel_button = Button(master=self.init_window,
                                       text='Cancel',
                                       width=20,
                                       command=self.init_window_close)
                cancel_button.grid(column=0,
                                   row=row,
                                   sticky=W)
                # Reset reference when child is closed
                self.init_window.protocol("WM_DELETE_WINDOW", self.init_window_close)

    def init_window_close(self):
        """Reset reference when the child window is closed."""
        if self.init_window is not None:
            self.init_window.destroy()
            self.init_window = None
            self.window.deiconify()

    def ok_change_password_window(self) -> None:
        """
        Passwords entered in change password window. Now proceed
        :return: None
        """
        p1 = self.change_password1.get()
        p2 = self.change_password2.get()
        if p1 != p2:
            messagebox.showinfo("Error", "Passwords do not match")
        else:
            cmd = "gocryptfs -passwd " + self.path_to_gocryptfs
            p_old = self.password.get()
            logger.debug(cmd)
            child = pexpect.spawn(cmd)

            try:
                child.expect("Password:", timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))
            child.sendline(p_old)

            try:
                child.expect("Password:", timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))
            child.sendline(p1)

            try:
                child.expect("Repeat:", timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))
            child.sendline(p2)

            try:
                child.expect(pexpect.EOF, timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))

            output = child.before.decode()
            output_clean = remove_esc(output)
            messagebox.showinfo("Change Password", output_clean)

        self.change_password_window_close()

    def ok_init_window(self) -> None:
        """
        Passwords entered in init window now proceed
        :return: None
        """
        p1 = self.init_password1.get()
        p2 = self.init_password2.get()
        if p1 != p2:
            messagebox.showinfo("Error", "Passwords do not match")
        else:
            cmd = "gocryptfs -init " + self.path_to_gocryptfs
            logger.debug(cmd)
            child = pexpect.spawn(cmd)
            try:
                child.expect("Password:", timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))
            child.sendline(p1)

            try:
                child.expect("Repeat:", timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))
            child.sendline(p2)

            try:
                child.expect(pexpect.EOF, timeout=2)
            except pexpect.exceptions.EOF:
                messagebox.showinfo("Error", str(child))

            output = child.before.decode()
            output_clean = remove_esc(output)
            self.show_master_key_window(output_clean)

        self.init_window_close()
