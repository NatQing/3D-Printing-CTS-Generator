# import modules
from datetime import datetime
from tkinter import *
from tkinter import ttk

from matplotlib.transforms import Bbox
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

# constants:##################################################################################################################################################################################################
# too lazy to change all vars into capital globals :/
#VAR PREWRITTEN FOR CTS
HOME = 'G28'            # this is a custom saved location
positioning = 'G90'     # absolute positioning
units = 'G21'           # everything using mm
extrusion_type = 'M83'  # Relative is good for speed; M82 Abs is good for setting volume

# settings:
material = 'PCL'    # purely informational, does not affect printer function
printer = 'Voron'   # purely informational
nozzle_temp = 230   # C probably depends on material...
bed_temp = 40       # C, target is 37C but water dissipates some

# platform limits(be aware that it could go over if inaccurate)
x_max = 120  # mm
y_max = 120  # mm

# Line Settings: How wide and tall for the box of lines: in mm
product_width = 50      # mm SHOULD NOT BE GREATER THAN X_MAX
product_height = 40     # mm SHOULD NOT BE GREATER THAN Y_MAX
num_groups = 2          # number of line groups - consecutive lines made with same speed
line_per_group = 2      # mm gap between lines of the same line group
ratio_of_dxgroup_dxline = 2  # ratio between distance between lines and distance between groups of lines so dxg/dxl

# one dir printing doesnt rly work since it adds new points to traverse. :/
one_dir_printing = 0
start_in_reverse = 0
transpose_graph = 0

# for incrementing pts only:
pts_per_line = 4    # mm Choose 1mm if you want each whole line representing one speed.

# testing all feeding speeds within range:
extrude_vmin = 0.2  # mm/min
extrude_vmax = 1    # mm/min
nozzle_v_cap = 50   # mm/min

velocity_of_nozzle = 600  # mm/min
velocity_of_nozzle_cap = 800  # mm/min
bed_dist = 5       # mm
raise_height = 4    # mm

flathead_nozzle_width = 10  # mm

#these were for resource usage calc. not Used
mm_to_ml_constant = 48
gear_ratio_constant = -1  # mm/mm changed settings in printer.cfg
cylinder_length_per_volume = 5.53  # obtain from measuring distance between syringe indents mm/ml
mm_stepper_per_ml_syringe = cylinder_length_per_volume / gear_ratio_constant  # mm_stepper/ml_syringe


use_collagen = 0
use_flathead = 0

# stuff i just need here:
figure = Figure(figsize=(2.5, 3.0), dpi=190)
spliced_plot = figure.add_subplot(111)
list_of_boxes = []

spliced_coordinate = []
input_coordinate = []
speed_corresponding_to_spliced_coord = []
z_list = []

# use for nxn product
def get_coordinate_init_centered(width, height, dx_line, x_max, y_max):
    # always want the product to be centered, cannot go beyond the limit
    if (transpose_graph): y_max, x_max = x_max, y_max
    x_init, y_init = x_max - width, y_max - height
    if dx_line == 0: x_init, y_init = x_max, y_max - height
    return np.array([x_init, y_init])/2

def splice_vector_into_pts(xy_init, xy_final, pts_per_line):
    result = np.linspace(xy_init, xy_final, pts_per_line)
    return result

def draw_rect(set):
    start = (input_coordinate[set][0] - flathead_nozzle_width / 2, input_coordinate[set][1])
    width = (flathead_nozzle_width)
    height = (input_coordinate[set + 1][1] - input_coordinate[set][1])
    if (transpose_graph):
        start = (input_coordinate[set][0], input_coordinate[set][1] - flathead_nozzle_width / 2)
        height = width
        width = (input_coordinate[set + 1][0] - input_coordinate[set][0])
    box = Rectangle(start, width, height, facecolor="none", edgecolor="red")
    list_of_boxes.append(box)


# gcode writer that will combine coordinate information and speed information
def get_gcode_block(position, filament_speed, height):
    return f"G1 E{filament_speed} F{velocity_of_nozzle} X{position[0]} Y{position[1]} Z{height}"

def get_gcode_block_movement_only(position, filament_speed, height):
    return f"G0 F{velocity_of_nozzle} X{position[0]} Y{position[1]} Z{height}"

def find_dx_line():
    try: result = product_width / (num_groups * (line_per_group - 1) + ratio_of_dxgroup_dxline * (num_groups - 1))
    except ZeroDivisionError: result = 0
    return result


##################################################################################################################################################################################################

def find_path():
    global input_coordinate

    dx_line = find_dx_line()
    dx_group = dx_line * ratio_of_dxgroup_dxline
    print(f"Distance between lines: {dx_line}mm")
    print(f"Distane between groups: {dx_group}mm")
    
    coord_init = get_coordinate_init_centered(product_width, product_height, dx_line, x_max, y_max)

    if use_flathead:
        dx_line = product_width / (num_groups + 1)
    if (flathead_nozzle_width > dx_line):
        print("Potential Overlap Detected!")
    else:
        print("No Overlap Detected!")

    input_coordinate = []
    if (start_in_reverse):
        input_coordinate.append((coord_init[0], coord_init[1] + product_height))
    else:
        input_coordinate.append(coord_init)

    def find_next_pt(input, viable_opt):
        if input == viable_opt[0]:
            return viable_opt[1]
        return viable_opt[0]

    for group in range(int(num_groups)):
        options = [coord_init[1], coord_init[1] + product_height]
        for line in range(int(line_per_group)):
            current_x, current_y = (input_coordinate[-1])
            next_pt = [current_x, find_next_pt(current_y, options)]
            input_coordinate.append(next_pt)
            # If one-dir is toggled
            if (one_dir_printing):
                current_x, current_y = (input_coordinate[-1])
                next_pt = [current_x, find_next_pt(current_y, options)]
                input_coordinate.append(next_pt)
            # If this is NOT last line of group
            if line != line_per_group - 1:
                current_x, current_y = (input_coordinate[-1])
                next_pt = [current_x + dx_line, current_y]
                input_coordinate.append(next_pt)
        current_x, current_y = (input_coordinate[-1])
        if group != num_groups - 1:
            input_coordinate.append([current_x + dx_group, current_y])

    input_coordinate = np.array(input_coordinate)
    if (transpose_graph):
        input_coordinate = np.flip(input_coordinate, 1)


##################################################################################################################################################################################################

def do_splice():
    global spliced_coordinate, spliced_plot
    spliced_plot.clear()
    spliced_coordinate = np.array([input_coordinate[0]])
    print(spliced_coordinate)
    
    units_to_skip = 2
    if (one_dir_printing):
        units_to_skip = 3
    
    for set in range(1, len(input_coordinate), units_to_skip):
        spliced_vector = splice_vector_into_pts(input_coordinate[set-1], input_coordinate[set], int(pts_per_line))
        spliced_coordinate = np.vstack((spliced_coordinate, spliced_vector))
        
        if one_dir_printing:
            #skipping a step forward:
            spliced_coordinate = np.vstack((spliced_coordinate, input_coordinate[set+1]))
        if use_flathead:
            draw_rect(set)
    spliced_coordinate = np.delete(spliced_coordinate, 0, 0)
    print(spliced_coordinate)


def calc_speeds():
    speed_corresponding_to_spliced_coord = []
    # create array for each point's speed
    v_list_length = (pts_per_line-1)*line_per_group*num_groups
    speed_distribution = np.linspace(extrude_vmin, extrude_vmax, v_list_length) * -1
    if len(speed_distribution) == len(spliced_coordinate): return speed_distribution
    for lines in range(0,line_per_group*num_groups):
        new_segment = speed_distribution[lines*(pts_per_line-1):(lines+1)*(pts_per_line-1)].tolist()
        if one_dir_printing:
            new_segment.append(0)
        new_segment.append(0)
        speed_corresponding_to_spliced_coord = np.append(speed_corresponding_to_spliced_coord, new_segment, 0)
    return speed_corresponding_to_spliced_coord

###GUI stuff mostly

do_refresh = 1

def clear():
    for ids in root.tk.eval('after info').split():
        root.after_cancel(ids)

def make_entry(root, comment):
    entry_label = Label(root, text=comment)
    entry_label.pack()
    entry = Entry(root, text=comment)
    entry.pack()
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
    widget.config(state="disabled")


def show_entry(widget):
    widget['state'] = "normal"


def dress_graph(graph):
    graph.draw()
    graph.get_tk_widget().pack()
    toolbar = NavigationToolbar2Tk(graph, right_frame, pack_toolbar=False)
    toolbar.update()


def undress_graph(graph):
    graph.get_tk_widget().pack_forget()


def auto_fill(widget, text):
    try:
        widget.delete(0, END)
        widget.insert(0, text)
        return True
    except:
        return False

def upload_entries():
    global product_width, product_height, num_groups, line_per_group, extrude_vmin, extrude_vmax, velocity_of_nozzle
    try:
        product_width = float(width.get())
        product_height = float(height.get())
        num_groups = int(groups.get())
        line_per_group = int(lpg.get())
        extrude_vmin = float(v_min.get())
        extrude_vmax = float(v_max.get())
        velocity_of_nozzle = float(v_nozzle.get())
    except ValueError:
        print("Error in Values")

def upload_bools():
    global use_flathead, use_collagen, one_dir_printing, transpose_graph, start_in_reverse
    use_collagen = collagen_mode.get()
    use_flathead = flathead_mode.get()
    one_dir_printing = one_dir_mode.get()
    transpose_graph = transpose_mode.get()
    start_in_reverse = reverse_start_mode.get()

def refresh():
    global use_flathead, use_collagen, do_refresh
    if do_refresh == False or var.get() > 200: return
    var.set(var.get() +1)
    
    upload_bools()
    
    if (flathead_mode.get()):
        auto_fill(lpg, 1)
        hide_entry(lpg)
    else:
        show_entry(lpg)

    root.after(500, refresh)


def send_print():
    global do_refresh
    upload_entries()
    do_refresh = 0
    root.quit()
    root.destroy()


def do_CTS():
    print("Using Local CTS Settings")
    auto_fill(width, product_width)
    auto_fill(height, product_height)
    auto_fill(groups, num_groups)
    auto_fill(lpg, line_per_group)
    auto_fill(v_nozzle, velocity_of_nozzle)
    auto_fill(v_max, extrude_vmax)
    auto_fill(v_min, extrude_vmin)

##################################################################################################################################################################################################
def update_graph():
    global do_refresh, list_of_boxes, graph, z_list, speed_corresponding_to_spliced_coord
    
    undress_graph(graph)
    list_of_boxes.clear()

    upload_entries()

    # Clear the previous plot

    # recalculate
    find_path()

    do_splice()

    speed_corresponding_to_spliced_coord = calc_speeds()
    
    
    z_list = np.zeros(len(spliced_coordinate))
    z_list.fill(bed_dist)

    # Update the plot
    spliced_plot.set_aspect('equal', adjustable='box')

    x = spliced_coordinate[:, 0]
    y = spliced_coordinate[:, 1]
    # this plots the points themselves
    spliced_plot.set_xlim([0, x_max])
    spliced_plot.set_ylim([0, y_max])
    # here is each spliced segment plotted in different colors and labeled
    colors = plt.cm.Spectral(np.linspace(0,1,num_groups*line_per_group*(pts_per_line-1)))
    spliced_plot.set_prop_cycle('color', colors)
    for index in range(1,len(spliced_coordinate)):
        temp = spliced_coordinate[index-1:index+1]
        #checking if index has corresponding speed assigned to it
        try:
            print(f"ACQUIRED FOR #{index-1} - #{index}: {speed_corresponding_to_spliced_coord[index-1]}")
        except:
            print(f"MISSING FOR #{index-1} - #{index}")
        #plotting segments: grey dashed is no printing
        if speed_corresponding_to_spliced_coord[index-1] == 0:
            spliced_plot.plot(temp[:, 0], temp[:, 1], color = "grey", ls = (0,(1,1)))
        else:
            spliced_plot.plot(temp[:, 0], temp[:, 1], label=round(speed_corresponding_to_spliced_coord[index-1],2)*-1)
    spliced_plot.set_position([0.1526641340346775, 0.187, 0.719671731930645, 0.6930000000000001])  # idk it just looks good on the gui
    legend = spliced_plot.legend(fontsize=3, loc='upper center', bbox_to_anchor=(0.5, 0), ncols=num_groups)
    # boxes
    for box in list_of_boxes:
        spliced_plot.add_patch(box)
    spliced_plot.scatter(x, y, s=20-pow(z_list,2)/9)
    spliced_plot.set_title("Print Path")
    plt.tight_layout()
    
    # scrolling section
    d = {"down": 20, "up": -20}
    def func(evt):
        if legend.contains(evt):
            bbox = legend.get_bbox_to_anchor()
            bbox = Bbox.from_bounds(bbox.x0, bbox.y0+d[evt.button], bbox.width, bbox.height)
            tr = legend.axes.transAxes.inverted()
            legend.set_bbox_to_anchor(bbox.transformed(tr))
            figure.canvas.draw_idle()
    figure.canvas.mpl_connect("scroll_event", func)
    
    # Redraw the canvas
    graph.draw()
    dress_graph(graph)


########################################################################################################################

# Create the GUI window
root = Tk()
root.geometry("800x650")
root.title("Settings")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.place(x=0, y=0)
left_frame = ttk.Labelframe(root, padding="9 9 12 12")
left_frame.place(x=20, y=2.5)
right_frame = ttk.Labelframe(root, text="PREVIEW:", padding="3 3 12 12")
right_frame.place(x=280, y=2.5)

graph = FigureCanvasTkAgg(figure, master=right_frame)
graph.get_tk_widget().place()

var = IntVar()
collagen_mode = BooleanVar()
flathead_mode = BooleanVar()
transpose_mode = BooleanVar()
one_dir_mode = BooleanVar()
reverse_start_mode = BooleanVar()

use_collagen = make_check(left_frame, "Collagen Mode", collagen_mode)
use_flathead = make_check(left_frame, "Use Flathead Nozzle", flathead_mode)
use_transpose = make_check(left_frame, "Transpose Graph", transpose_mode)
use_one_dir = make_check(left_frame, "Only print in one Direction", one_dir_mode)
use_start_reverse = make_check(left_frame, "Start in reversed Y", reverse_start_mode)
width = make_entry(left_frame, "Product Width[mm]: ")
height = make_entry(left_frame, "Product Height[mm]: ")
groups = make_entry(left_frame, "Number of Groups: ")
lpg = make_entry(left_frame, "Number of Lines/Group: ")
v_min = make_entry(left_frame, "Minimum Extrusion Speed[mm/s]: ")
v_max = make_entry(left_frame, "Maximum Extrusion Speed[mm/s]]: ")
v_nozzle = make_entry(left_frame, "Nozzle Movement Speed[mm/min]: ")
cts_button = make_button(left_frame, "Do CTS", do_CTS)
update_graph = make_button(left_frame, "Update Graph", update_graph)
create_button = make_button(left_frame, "Write File", send_print)

refresh()

root.mainloop()

print("running gcode convert section")
# create file:
if use_collagen:
    material = "collagen"
else:
    material = "PLA"

if use_flathead:
    nozzle = "flathead"
else:
    nozzle = "needle"

file_name = f"File_{material}_{nozzle}"
if len(file_name) > 1:
    with open(str(file_name) + ".gcode", "w") as f:
        # description
        f.write(";File Name: " + str(file_name))
        f.write("\n;Time Generated: " + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S')))  # get date
        f.write("\n;Printer Type: " + str(printer))
        f.write(f"\nIntended Material: {material}")
        f.write("\n;dimension of product: " + str(product_width) + "x" + str(product_height) + " mm")
        f.write("\n;details of product: " + str(num_groups) + " groups of " + str(line_per_group) + " lines each")
        f.write("\n;speed increment: " + str(extrude_vmin) + " to " + str(extrude_vmax) + " mm/min for " + str(
            len(speed_corresponding_to_spliced_coord)) + " pts total")
        # set up
        f.write(f"\n\n\n{positioning}")
        f.write(f"\n{units}")
        f.write(f"\n{extrusion_type}")
        f.write(f"\nG28\n\n")

        # nozzle stuff:
        if use_collagen:
            f.write(f"\nM140 S38\n")    #BED TEMP
        else:
            f.write(
                f"\nSET_HEATER_TEMPERATURE HEATER=extruder TARGET={nozzle_temp}\nTEMPERATURE_WAIT SENSOR=extruder MINIMUM={nozzle_temp} MAXIMUM={nozzle_temp + 10}\n")
            f.write(f"M190 S{bed_temp}\n\n")
        for i in range(len(spliced_coordinate)):
            coordinate = spliced_coordinate[i]
            speed = speed_corresponding_to_spliced_coord[i-1]
            elevation = z_list[i]
            line = get_gcode_block(coordinate, speed, elevation)
            f.write(f"\n{line}")

        # ending code here
        if not use_collagen:
            f.write("\n\n\nM104 T0 S0\nM140 S0\nM84")
        f.write("\nM30\n;end of code")
clear()
exit()
