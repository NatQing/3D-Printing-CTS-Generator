#this will forever be a test page cuz it sucks lol
from tkinter import *

def run_GUI():
    entries = []
    result = []

    def make_entry(root, comment):
        entry_label = Label(root, text=comment)
        entry_label.pack()
        entry = Entry(root, text=comment)
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
    
    def hide_entry(widget):
        widget.config(state = "disabled")

    def show_state():
        result.clear()
        print(chr(27) + "[2J")
        
        if(collagen_mode.get()): print("Collagen Mode")
        else: print("Using PLA")
        
        if(flathead_mode.get()):
            print("Flathead Mode")
            do_flathead
        else: print("Regular Nozzle")
        
        for entry in entries:
            if(entry['state'] == "normal"):
                try:
                    number = float(entry.get())
                    print(f"Entered: {number}")
                    result.append(number)
                except ValueError:
                    print("Please enter a valid number")
            else: result.insert(0, -1)
        result.append(collagen_mode.get())
        result.append(flathead_mode.get())

    def upload_settings():
        print("Uploading!")
        root.destroy()
        
    def do_CTS():
        print("Using Local CTS Settings")
        auto_fill(width, -1)
        auto_fill(height, -1)
        auto_fill(groups, -1)
        auto_fill(line_per_group, -1)
        hide_entry(width)
        hide_entry(height)
        hide_entry(groups)
        hide_entry(line_per_group)
        
    def do_flathead():
        print("Switched to Flathead mode")
        hide_entry(line_per_group)
        auto_fill(groups, "Enter Number of Sheets Here")
    
    def auto_fill(widget, text):
        widget.delete(0, -1)
        widget.insert(0, text)

    # Create the main window
    
    
    root = Tk()
    root.minsize(400,500)
    root.title("CTS Settings")


    collagen_mode = BooleanVar()
    flathead_mode = BooleanVar()
    
    use_collagen = make_check(root, "Collagen Mode", collagen_mode)
    use_flathead = make_check(root, "Use Flathead Nozzle", flathead_mode)

    width = make_entry(root, "Product Width[mm]: ")
    height = make_entry(root, "Product Height[mm]: ")
    groups = make_entry(root, "Number of Groups: ")
    line_per_group = make_entry(root, "Number of Lines/Group: ")
    v_min = make_entry(root, "Minimum Extrusion Speed[mm/s]: ")
    v_max = make_entry(root, "Maximum Extrusion Spee[mm/s]]: ")
    v_nozzle = make_entry(root, "Nozzle Movement Speed[mm/s]: ")

    cts_button = make_button(root, "Do CTS", do_CTS)
    #flathead_button = make_button(root, "Use Flathead", flathead_mode)
    update_button = make_button(root, "Check Inputs", show_state)
    create_button = make_button(root, "Write File", upload_settings)
    
    #print(update_button.config('text')[-1])
    
    root.mainloop()
    if len(result) < 1: print("Empty input.")
    #print(result + [collagen_mode.get(), flathead_mode.get()])
    return result