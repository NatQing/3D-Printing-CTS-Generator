#import modules
import matplotlib.pyplot as plt, numpy as np, math
from matplotlib.patches import Rectangle
from datetime import datetime
from matplotlib.figure import Figure
from tkinter import *
from tkinter import ttk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)


#constants:##################################################################################################################################################################################################
HOME = 'G28'        #this is a custom saved location
positioning = 'G90' #absolute positioning
units = 'G21'       #everything using mm
extrusion_type = 'M83'  #Relative is good for speed; M82 Abs is good for setting volume

#settings:
material = 'PCL'    #purely informational, does not affect printer function
printer = 'Voron'   #purely informational
nozzle_temp = 230   #C probably depends on material...
bed_temp = 35       #C sometimes will get stuck if above 40

#platform limits(be aware that it could go over if inaccurate)
x_max = 101     #mm
y_max = 118     #mm


#Line Settings: How wide and tall for the box of lines: in mm
product_width = 50  #mm SHOULD NOT BE GREATER THAN X_MAX
product_height = 40 #mm SHOULD NOT BE GREATER THAN Y_MAX
num_groups = 5     #number of line groups - consecutive lines made with same speed
line_per_group = 2  #mm gap between lines of the same line group
ratio_of_dxgroup_dxline = 2 #ratio between distance between lines and distance between groups of lines so dxg/dxl

#for incrementing pts only:
pts_per_line = 5    #mm Choose 1mm if you want each whole line representing one speed.

#testing all feeding speeds within range:
nozzle_v_min = 0.2      #mm/min
nozzle_v_max = 1       #mm/min
nozzle_v_cap = 5       #mm/min

velocity_of_nozzle = 400    #mm/min
velocity_of_nozzle_cap = 800    #mm/min
bed_dist = -1  #mm


collagen = 0    #new material
flathead = 0    #new nozzle

flathead_nozzle_width = 10   #mm

gear_ratio_constant = -1 #mm/mm changed settings in printer.cfg
cylinder_length_per_volume = 5.53   #obtain from measuring distance between syringe indents mm/ml
mm_stepper_per_ml_syringe = cylinder_length_per_volume/gear_ratio_constant  #mm_stepper/ml_syringe
print(mm_stepper_per_ml_syringe)

#stuff i just need here:
figure = Figure(figsize=(2.5,2.5), dpi=190)
spliced_plot= figure.add_subplot(111)

#use for nxn product
def get_coordinate_init_centered(product_width, product_height):
    #always want the product to be centered, cannot go beyond the limit
    coord_init = np.array([x_max-product_width,y_max-product_height])/2
    return coord_init

def find_next_pt(input, viable_opt):
    if(input == viable_opt[0]):
        return viable_opt[1]
    return viable_opt[0]

def splice_vector_into_pts(xy_init, xy_final, pts_per_line):
    result = np.linspace(xy_init,xy_final,pts_per_line)
    return result

#gcode writer that will combine coordinate information and speed information
def get_gcode_block(position, fillament_speed):
    return f"G1 X{position[0]} Y{position[1]} Z{bed_dist} E{fillament_speed}"

def get_gcode_block_movement_only(position, filament_speed):
     return f"G1 X{position[0]} Y{position[1]} Z{bed_dist}"

##################################################################################################################################################################################################


#this will forever be a test page cuz it sucks lol

do_refresh = 1

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
    widget.config(state = "disabled")

def show_entry(widget):
    widget['state'] = "normal"

def dress_graph(graph):
    graph.draw()
    graph.get_tk_widget().pack()
    toolbar = NavigationToolbar2Tk(graph, right_frame, pack_toolbar=False)
    toolbar.update()

def undress_graph(graph):
    graph.get_tk_widget().pack_forget()

def refresh():
    global do_refresh
    if not do_refresh: return
    
    undress_graph(graph)
    dress_graph(graph)
    
    if(collagen_mode.get()):
        print("Collagen Mode")
    else: print("Using PLA")
    
    if(flathead_mode.get()):
        print("Flathead Mode")
        auto_fill(lpg, 1)
        hide_entry(lpg)
    else: 
        print("Regular Nozzle")
        show_entry(lpg)
    
    root.after(500, refresh)
    

def upload_settings():
    print("Uploading!")
    product_width = width.get()
    product_height = height.get()
    num_groups = groups.get()
    line_per_group = lpg.get()
    nozzle_v_min = v_min.get()
    nozzle_v_max = v_max.get()
    velocity_of_nozzle = v_nozzle.get()
    collagen = collagen_mode.get()
    flathead = flathead_mode.get()
    
    global do_refresh
    do_refresh = 0
    root.destroy()
    
def do_CTS():
    print("Using Local CTS Settings")
    auto_fill(width, product_width)
    auto_fill(height, product_height)
    auto_fill(groups, num_groups)
    auto_fill(lpg, line_per_group)

##################################################################################################################################################################################################
def update_graph():
    global do_refresh
    do_refresh = 0
    print("trying")
    
    try:
        product_width = float(width.get())
        product_height = float(height.get())
        num_groups = float(groups.get())
        line_per_group = float(lpg.get())
        nozzle_v_min = float(v_min.get())
        nozzle_v_max = float(v_max.get())
        velocity_of_nozzle = float(v_nozzle.get())
        collagen = collagen_mode.get()
        flathead = flathead_mode.get()
    except ValueError:
        print("Error in Values")
    
    # Clear the previous plot
    spliced_plot.clear()
    
    # Recalculate the necessary values
    dx_line = product_width / (num_groups * (line_per_group - 1) + ratio_of_dxgroup_dxline * (num_groups - 1))
    dx_group = dx_line * ratio_of_dxgroup_dxline
    
    if flathead:
        dx_line = product_width/(num_groups+1)
    
    input_coordinate = []
    coord_init = get_coordinate_init_centered(product_width, product_height)
    print(coord_init)
    input_coordinate.append(coord_init)
    
    for group in range(int(num_groups)):
        options = [coord_init[1], coord_init[1] + product_height]
        for line in range(int(line_per_group)):
            current_x = (input_coordinate[-1])[0]
            current_y = (input_coordinate[-1])[1]
            next_pt = [current_x, find_next_pt(current_y, options)]
            input_coordinate.append(next_pt)
            if line != line_per_group - 1:
                current_x = (input_coordinate[-1])[0]
                current_y = (input_coordinate[-1])[1]
                next_pt = [current_x + dx_line, current_y]
                input_coordinate.append(next_pt)
        current_x = (input_coordinate[-1])[0]
        current_y = (input_coordinate[-1])[1]
        if group != num_groups - 1:
            input_coordinate.append([current_x + dx_group, current_y])
    
    input_coordinate = np.array(input_coordinate)
    
    spliced_coordinate = np.array([coord_init])
    list_of_boxes = []
    
    for set in range(0, len(input_coordinate) - 1, 2):
        spliced_vector = splice_vector_into_pts(input_coordinate[set], input_coordinate[set + 1], int(pts_per_line))
        spliced_coordinate = np.concatenate((spliced_coordinate, spliced_vector), axis=0)
        if flathead:
            box = Rectangle((input_coordinate[set][0] - flathead_nozzle_width / 2, input_coordinate[set][1]),
                            (flathead_nozzle_width), (input_coordinate[set + 1][1] - input_coordinate[set][1]),
                            facecolor="none", edgecolor="red")
            list_of_boxes.append(box)
    
    spliced_coordinate = np.delete(spliced_coordinate, 0, 0)
    
    # Update the plot
    spliced_plot.set_aspect('equal', adjustable='box')
    spliced_plot.scatter(spliced_coordinate[0][0], spliced_coordinate[0][1])
    x = spliced_coordinate[:, 0]
    y = spliced_coordinate[:, 1]
    spliced_plot.set_xlim([0, x_max])
    spliced_plot.set_ylim([0, y_max])
    spliced_plot.plot(x, y)
    for box in list_of_boxes:
        spliced_plot.add_patch(box)
    spliced_plot.scatter(x, y, s=3)
    spliced_plot.set_title("spliced")
    plt.show()
    
    # Redraw the canvas
    graph.draw()
    
    # Avoid packing the widget multiple times
    # graph.get_tk_widget().pack()

    do_refresh = 1

###################################################################################################################################################################################################################################################################################################

def auto_fill(widget, text):
    widget.delete(0, END)
    widget.insert(0, text)

# Create the main window


root = Tk()
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.place(x=0, y=0)

left_frame = ttk.Labelframe(root, padding="9 9 12 12")
left_frame.place(x=20, y=2.5)

right_frame = ttk.Labelframe(root, text="Results:", padding="3 3 12 12")
right_frame.place(x=280, y=2.5)

root.geometry("800x550")
root.title("Settings")

graph = FigureCanvasTkAgg(figure, master = right_frame)
graph.get_tk_widget().place()

collagen_mode = BooleanVar()
flathead_mode = BooleanVar()

use_collagen = make_check(left_frame, "Collagen Mode", collagen_mode)
use_flathead = make_check(left_frame, "Use Flathead Nozzle", flathead_mode)
width = make_entry(left_frame, "Product Width[mm]: ")
height = make_entry(left_frame, "Product Height[mm]: ")
groups = make_entry(left_frame, "Number of Groups: ")
lpg = make_entry(left_frame, "Number of Lines/Group: ")
v_min = make_entry(left_frame, "Minimum Extrusion Speed[mm/s]: ")
v_max = make_entry(left_frame, "Maximum Extrusion Spee[mm/s]]: ")
v_nozzle = make_entry(left_frame, "Nozzle Movement Speed[mm/s]: ")

cts_button = make_button(left_frame, "Do CTS", do_CTS)
update_graph = make_button(left_frame, "Update Graph", update_graph)
create_button = make_button(left_frame, "Write File", upload_settings)

refresh()

root.mainloop()

#Calculations:
dx_line = product_width/(num_groups*(line_per_group-1)+ratio_of_dxgroup_dxline*(num_groups-1))  #mm
print(f"Distance between lines: {dx_line}mm")
dx_group = dx_line*ratio_of_dxgroup_dxline  #mm
print(f"Distane between groups: {dx_group}mm")

nozzle_dv = (nozzle_v_max-nozzle_v_min)/num_groups   #mm/s

if flathead:
    dx_line = product_width/(num_groups+1)
    if(flathead_nozzle_width > dx_line): print("Potential Overlap Detected!")
    else: print("No Overlap Detected!")

#Coordinate plotting:
input_coordinate = []

coord_init = get_coordinate_init_centered(product_width, product_height)

#generate rough lines, then can populate new coordinate list with linspaced points for increments

#generating lines w/out increment:
input_coordinate.append(coord_init)
for group in range(int(num_groups)):
    options = [coord_init[1], coord_init[1]+product_height]
    for line in range(int(line_per_group)):
        
        current_x = (input_coordinate[-1])[0]
        current_y = (input_coordinate[-1])[1]
        next_pt = [current_x,find_next_pt(current_y,options)]
        input_coordinate.append(next_pt)
        
        if line != line_per_group-1:
            current_x = (input_coordinate[-1])[0]
            current_y = (input_coordinate[-1])[1]
            next_pt = [current_x+dx_line, current_y]
            input_coordinate.append(next_pt)
        
    current_x = (input_coordinate[-1])[0]
    current_y = (input_coordinate[-1])[1]
    if group != num_groups-1:
        input_coordinate.append([current_x+dx_group,current_y])

input_coordinate = np.array(input_coordinate)
#print(input_coordinate)
print(len(input_coordinate))

#incrementize coordinates:
spliced_coordinate = np.array([coord_init])
list_of_boxes = []

for set in range(0, len(input_coordinate)-1, 2):
    spliced_vector = splice_vector_into_pts(input_coordinate[set],input_coordinate[set+1],int(pts_per_line))
    spliced_coordinate = np.concatenate((spliced_coordinate,spliced_vector),axis=0)
    if(flathead):
        box = Rectangle((input_coordinate[set][0]-flathead_nozzle_width/2,input_coordinate[set][1]), (flathead_nozzle_width), (input_coordinate[set+1][1]-input_coordinate[set][1]), facecolor = "none", edgecolor = "red")
        list_of_boxes.append(box)
    

spliced_coordinate = np.delete(spliced_coordinate,0,0)


spliced_plot.set_aspect('equal', adjustable='box')
spliced_plot.scatter(spliced_coordinate[0][0],spliced_coordinate[0][1])
x = spliced_coordinate[:,0]
y = spliced_coordinate[:,1]
plt.axis([0, x_max, 0, y_max])
spliced_plot.plot(x,y)
ax = plt.gca()
for box in list_of_boxes:
    ax.add_patch(box)
spliced_plot.scatter(x,y, s=3)
plt.title("spliced")


#create array for each point's speed
speed_corresponding_to_spliced_coord = np.linspace(nozzle_v_min,nozzle_v_max,len(spliced_coordinate))*-1
#print(speed_corresponding_to_spliced_coord)
print(len(speed_corresponding_to_spliced_coord))
print(f"Material Usage: {(nozzle_v_max-nozzle_v_min)*mm_stepper_per_ml_syringe}mL")


#create file:

file_name = input("Enter file name: ")
if(len(file_name) > 1): 
    with open(str(file_name) + ".gcode", "w") as f:
    #description
        f.write(";File Name: " + str(file_name))
        f.write("\n;Time Generated: " + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S')))  #get date
        f.write("\n;Printer Type: " + str(printer))
        f.write("\n;dimension of product: " + str(product_width) +"x"+ str(product_height) +" mm")
        f.write("\n;details of product: " + str(num_groups) +" groups of "+ str(line_per_group) +" lines each")
        f.write("\n;speed increment: " + str(nozzle_v_min) +" to "+ str(nozzle_v_max) +" mm/min for " +str(len(speed_corresponding_to_spliced_coord)) +" pts total")
        #set up
        f.write(f"\n\n\n{positioning}")
        f.write(f"\n{units}")
        f.write(f"\n{extrusion_type}")
        f.write(f"\nG28 F{velocity_of_nozzle} Z{bed_dist}")


        #nozzle stuff:
        if(not collagen):
                f.write(f"\nSET_HEATER_TEMPERATURE HEATER=extruder TARGET={nozzle_temp}\nTEMPERATURE_WAIT SENSOR=extruder MINIMUM={nozzle_temp} MAXIMUM={nozzle_temp+10}\n")
                f.write(f"M190 S{bed_temp}\n\n")
        for i in range(len(spliced_coordinate)):
                line = get_gcode_block(spliced_coordinate[i],speed_corresponding_to_spliced_coord[i])
                f.write(f"\n{line}")

        #ending code here
        if(not collagen):
                f.write("\n\n\nM104 T0 S0\nM140 S0\nM84")
        f.write("\nM30\n;end of code")

