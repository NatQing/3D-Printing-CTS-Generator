from tkinter import *

def run_GUI():
    entries = []
    result = []

    def make_entry(root, comment):
        entry_label = Label(root, text=comment)
        entry_label.pack()
        entry = Entry(root)
        entry.pack()
        entries.append(entry)
        return entry
        
    def make_check(root, comment, var):
        # Create the main window
        checkbutton = Checkbutton(root, text=comment, variable=var)
        checkbutton.pack()
        return checkbutton
        
    def make_button(root, comment, command):
        button = Button(root, text=comment, relief="raised", command=command)
        button.pack()
        return button

    def show_state():
        result.clear()
        print(chr(27) + "[2J")
        if check_mark.get():
            print("Using Collagen!")
        else:
            print("Not Using Collagen!")
        
        for entry in entries:
            try:
                number = float(entry.get())
                print(f"Entered number: {number}")
                result.append(number)
            except ValueError:
                print("Please enter a valid number")
        print(result)
        

    def upload_settings():
        print("Uploading!")
        root.destroy()


    # Create the main window
    
    
    root = Tk()
    root.minsize(400,500)
    root.title("CTS Settings")


    check_mark = BooleanVar()
    switch = make_check(root, "Printing Collagen? [not functional yet]", check_mark)

    width = make_entry(root, "Product Width[mm]: ")
    height = make_entry(root, "Product Height[mm]: ")
    groups = make_entry(root, "# of Groups: ")
    line_per_group = make_entry(root, "# of Lines/Group: ")
    pts_per_line = make_entry(root, "Pts per Line: ")
    v_min = make_entry(root, "Minimum Extrusion Speed[mm/s]: ")
    v_max = make_entry(root, "Maximum Extrusion Spee[mm/s]]: ")
    v_nozzle = make_entry(root, "Nozzle Movement Speed[mm/s]: ")

    update_button = make_button(root, "Update!", show_state)
    create_button = make_button(root, "Write File", upload_settings)

    # Start the main event loop
    root.mainloop()
    return result